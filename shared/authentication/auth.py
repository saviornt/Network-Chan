"""Low-level authentication utilities for Network-Chan.

This module provides reusable, non-HTTP authentication primitives:
- Password hashing/verification (Argon2id)
- Password strength validation (zxcvbn + NIST/NSA rules)
- JWT creation/decoding
- TOTP secret generation, verification, and provisioning URI

All functions are pure (no DB or FastAPI dependencies) and designed to be
called from service layer or other modules.

Security notes:
- Uses Argon2id (memory-hard, configurable params from auth_settings)
- zxcvbn entropy estimation + common password blacklist
- JWT with subject, expiration, scopes
- TOTP follows RFC 6238 (6-digit, 30s interval by default)

No rate limiting is applied here — enforce at caller level (service/router).
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import List, Optional, Tuple

import pyotp
import zxcvbn
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from database.crud import get_user_by_username
from settings import auth_settings
from models.auth_model import TokenResponse, CurrentUser
from shared.utils.logging_factory import get_logger


logger = get_logger(__name__, category="auth")


pwd_context = CryptContext(
    schemes=["argon2"],
    deprecated="auto",
    argon2_type="id",
    argon2__time_cost=auth_settings.argon2_time_cost,
    argon2__memory_cost=auth_settings.argon2_memory_cost,
    argon2__parallelism=auth_settings.argon2_parallelism,
    argon2__hash_len=32,  # 256-bit output
)


# ──────────────────────────────────────────────────────────────────────────────
# Password Hashing (Argon2id – NIST/NSA preferred)
# ──────────────────────────────────────────────────────────────────────────────


def hash_password(password: str) -> str:
    """
    Hash a plaintext password using Argon2id.

    Args:
        password: Plaintext password to hash

    Returns:
        str: Argon2id-encoded hash string (prefixed with $argon2id$...)

    Raises:
        ValueError: If password is empty or None
    """
    if not password:
        raise ValueError("Password cannot be empty")
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plaintext password against an Argon2id hash.

    Args:
        plain_password: Plaintext password to check
        hashed_password: Stored Argon2id hash

    Returns:
        bool: True if password matches hash, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


# ──────────────────────────────────────────────────────────────────────────────
# Password Strength Validation (NIST SP 800-63B compliant)
# ──────────────────────────────────────────────────────────────────────────────


class PasswordValidationError(Exception):
    """Raised when password fails validation rules."""


class PasswordValidator:
    """
    Validates password strength per modern NIST/NSA recommendations.

    Features:
    - Minimum length check (12+ chars recommended)
    - Blacklist of common passwords
    - Personal data avoidance (username, user_data)
    - zxcvbn entropy scoring with feedback

    Usage:
        is_valid, feedback = password_validator.validate("my-strong-pass-2026")
    """

    def __init__(self) -> None:
        # Common passwords blacklist (extend with rockyou.txt / HIBP in production)
        self.common_passwords: set[str] = {
            "password",
            "123456",
            "admin",
            "letmein",
            "qwerty",
            "welcome",
            # TODO: Load ~10k most common passwords from file/resource
        }

    def validate(
        self,
        password: str,
        username: Optional[str] = None,
        user_data: Optional[List[str]] = None,
    ) -> Tuple[bool, List[str]]:
        """
        Validate password strength.

        Args:
            password: The password to check
            username: Optional username to avoid password == username
            user_data: Optional list of personal data (email, phone, birthdate, etc.)

        Returns:
            Tuple[bool, List[str]]: (is_valid, list of failure reasons or hints)
        """
        feedback: List[str] = []

        # 1. Minimum length
        if len(password) < 12:
            feedback.append("Password must be at least 12 characters long.")
        elif len(password) >= 16:
            feedback.append(
                "Good length — longer passwords are significantly stronger."
            )

        # 2. Not too common
        if password.lower() in self.common_passwords:
            feedback.append("This password is too common and likely breached.")

        # 3. Avoid personal data
        if username and password.lower() == username.lower():
            feedback.append("Password should not match your username.")
        if user_data:
            for item in user_data:
                if item and password.lower() == item.lower():
                    feedback.append("Password should not match personal information.")

        # 4. zxcvbn entropy estimation
        result = zxcvbn.zxcvbn(
            password,
            user_inputs=[username] + (user_data or []) if username else [],
        )

        if result["score"] < 3:
            feedback.append(
                f"Weak password strength (score {result['score']}/4). "
                "Add more unique words or increase length."
            )
        elif result["score"] >= 4:
            feedback.append("Strong password!")

        # Final decision
        is_valid = (
            len(password) >= 12
            and result["score"] >= 3
            and password.lower() not in self.common_passwords
        )

        return is_valid, feedback


# Singleton instance (reusable across the app)
password_validator = PasswordValidator()


def validate_password(
    password: str,
    username: Optional[str] = None,
    user_data: Optional[List[str]] = None,
) -> Tuple[bool, List[str]]:
    """
    Convenience wrapper around PasswordValidator.validate().

    Args:
        password: Password to validate
        username: Optional username context
        user_data: Optional additional personal data

    Returns:
        Tuple[bool, List[str]]: (is_valid, feedback list)
    """
    return password_validator.validate(password, username, user_data)


# ──────────────────────────────────────────────────────────────────────────────
# JWT (session / API tokens)
# ──────────────────────────────────────────────────────────────────────────────


def create_access_token(
    username: str,
    scopes: list[str] | None = None,
    expires_delta: timedelta | None = None,
) -> TokenResponse:
    """
    Create a new JWT access token for the given user.

    Args:
        username: Subject (sub) claim
        scopes: Optional list of scopes/permissions
        expires_delta: Optional custom expiration (defaults to config)

    Returns:
        TokenResponse with access_token, token_type, expires_in (seconds)

    Raises:
        ValueError: If username is empty
    """
    if not username:
        raise ValueError("Username cannot be empty")

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=auth_settings.jwt_access_token_expire_minutes
        )

    to_encode = {
        "sub": username,
        "exp": expire,
        "scopes": scopes or [],
    }

    access_token = jwt.encode(
        to_encode,
        auth_settings.jwt_secret.get_secret_value(),
        algorithm=auth_settings.jwt_algorithm,
    )

    logger.info(
        "JWT access token created",
        username=username,
        expires=expire.isoformat(),
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=int((expire - datetime.now(timezone.utc)).total_seconds()),
    )


async def decode_access_token(token: str, db: AsyncSession) -> CurrentUser:
    """
    Decode and validate a JWT access token.

    Args:
        token: Raw JWT string

    Returns:
        CurrentUser with username, scopes, totp_enabled

    Raises:
        HTTPException 401: Invalid/expired/missing claims token
    """
    try:
        payload = jwt.decode(
            token,
            auth_settings.jwt_secret.get_secret_value(),
            algorithms=[auth_settings.jwt_algorithm],
        )
        username = payload.get("sub")
        if username is None:
            raise JWTError("Missing subject (sub) claim")
        if not isinstance(username, str):
            raise JWTError("Subject claim must be a string")

        user = await get_user_by_username(db, username)

        if user is None:
            logger.warning("JWT subject not found in database", username=username)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
            )

        return CurrentUser(
            username=username,
            scopes=payload.get("scopes", []),
            totp_enabled=user.totp_enabled,
        )
    except JWTError as exc:
        logger.warning("JWT validation failed", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ──────────────────────────────────────────────────────────────────────────────
# TOTP (2FA) Utilities
# ──────────────────────────────────────────────────────────────────────────────


def generate_totp_secret() -> str:
    """
    Generate a new random base32-encoded TOTP secret.

    Returns:
        str: Base32 secret (suitable for pyotp.TOTP)
    """
    secret = pyotp.random_base32()
    logger.debug("Generated new TOTP secret")
    return secret


def verify_totp(secret: str, code: str) -> bool:
    """
    Verify a TOTP code against the user's secret.

    Args:
        secret: Base32-encoded TOTP secret
        code: 6-8 digit code from authenticator app

    Returns:
        bool: True if code is valid in current time window
    """
    totp = pyotp.TOTP(
        secret,
        digits=auth_settings.totp_digits,
        interval=auth_settings.totp_interval_seconds,
    )
    valid = totp.verify(code.strip())
    if valid:
        logger.debug("TOTP verification succeeded")
    else:
        logger.warning("TOTP verification failed")
    return valid


def get_totp_provisioning_uri(secret: str, username: str) -> str:
    """
    Generate otpauth:// URI for QR code scanning in authenticator apps.

    Args:
        secret: Base32 TOTP secret
        username: User's identifier (display name in authenticator)

    Returns:
        str: otpauth://totp/... URI
    """
    totp = pyotp.TOTP(
        secret,
        digits=auth_settings.totp_digits,
        interval=auth_settings.totp_interval_seconds,
    )
    uri = totp.provisioning_uri(
        name=username,
        issuer_name=auth_settings.totp_issuer,
    )
    logger.debug("Generated TOTP provisioning URI", username=username)
    return uri


# Public API exports (makes the module easier to import from)
__all__ = [
    "hash_password",
    "verify_password",
    "validate_password",
    "password_validator",
    "create_access_token",
    "decode_access_token",
    "generate_totp_secret",
    "verify_totp",
    "get_totp_provisioning_uri",
]
