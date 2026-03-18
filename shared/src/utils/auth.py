"""Shared authentication utilities for Network-Chan.

Provides JWT encoding/decoding, TOTP generation/verification, password strength validation,
and FastAPI dependencies.

Password validation follows modern NIST SP 800-63B and NSA recommendations:
- Minimum length (12+ chars recommended)
- No forced composition rules
- Blacklist common/breached passwords
- Entropy estimation via zxcvbn
- User-friendly feedback for setup/change-password flows

All utilities are designed to be reusable across Appliance and Assistant.
"""

from datetime import datetime, timedelta, timezone
from typing import List, Optional, Tuple

import pyotp
import zxcvbn
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from shared.src.config.auth_settings import auth_settings
from shared.src.models.auth_model import TokenResponse, CurrentUser
from shared.src.utils.logging_factory import get_logger

logger = get_logger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")  # Update path as needed
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
    Hash a plaintext password using Argon2id (NIST-preferred memory-hard function).

    Returns:
        str: Argon2id-encoded hash string
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plaintext password against an Argon2id hash.

    Returns:
        bool: True if the password matches the hash
    """
    return pwd_context.verify(plain_password, hashed_password)


# ──────────────────────────────────────────────────────────────────────────────
# Password Strength Validation (NIST SP 800-63B compliant)
# ──────────────────────────────────────────────────────────────────────────────


class PasswordValidationError(Exception):
    """Raised when password fails validation."""


class PasswordValidator:
    """
    Validates password strength according to modern NIST/NSA recommendations.

    Usage:
        is_valid, feedback = password_validator.validate("my-very-long-password-2026")
    """

    def __init__(self):
        # Load common passwords (can be extended with HIBP-style list in production)
        self.common_passwords: set[str] = {
            "password",
            "123456",
            "admin",
            "letmein",
            "qwerty",
            "welcome",
            # Add ~10,000 most common ones in production (from rockyou.txt, etc.)
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
            username: Optional username (to prevent password == username)
            user_data: Optional list of other data (email, phone, etc.) to check against

        Returns:
            Tuple[bool, List[str]]: (is_valid, list of failure reasons or success hints)
        """
        feedback: List[str] = []

        # 1. Minimum length
        if len(password) < 12:
            feedback.append("Password must be at least 12 characters long.")
        elif len(password) >= 16:
            feedback.append("Good length! Longer passwords are much stronger.")

        # 2. Not too common
        if password.lower() in self.common_passwords:
            feedback.append("This password is too common and has likely been breached.")

        # 3. Not based on username or personal data
        if username and password.lower() == username.lower():
            feedback.append("Password should not be the same as your username.")
        if user_data:
            for item in user_data:
                if item and password.lower() == item.lower():
                    feedback.append("Password should not match personal information.")

        # 4. Entropy estimation (zxcvbn)
        result = zxcvbn.zxcvbn(
            password,
            user_inputs=[username] + (user_data or []) if username else [],
        )

        if result["score"] < 3:
            feedback.append(
                f"Password strength is weak (score {result['score']}/4). "
                "Consider adding more unique words or length."
            )
        elif result["score"] >= 4:
            feedback.append("Strong password!")

        # Final decision (length + score + blacklist)
        is_valid = (
            len(password) >= 12
            and result["score"] >= 3
            and password.lower() not in self.common_passwords
        )

        return is_valid, feedback


# Singleton instance
password_validator = PasswordValidator()


def validate_password(
    password: str,
    username: Optional[str] = None,
    user_data: Optional[List[str]] = None,
) -> Tuple[bool, List[str]]:
    """
    Convenience function: validate password using the shared validator.

    Returns (is_valid, feedback list).
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
    Generate a new JWT access token.

    Returns TokenResponse with access_token and expiration details.
    """
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

    logger.info("JWT access token created", username=username, expires=expire)

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=int((expire - datetime.now(timezone.utc)).total_seconds()),
    )


def decode_access_token(token: str) -> CurrentUser:
    """
    Decode and validate JWT token, return authenticated user info.

    Raises HTTPException on failure.
    """
    try:
        payload = jwt.decode(
            token,
            auth_settings.jwt_secret.get_secret_value(),
            algorithms=[auth_settings.jwt_algorithm],
        )
        username = payload.get("sub")
        if username is None:
            raise JWTError("Missing subject claim in token payload")
        if not isinstance(username, str):
            raise JWTError("Subject claim is not a string")
        return CurrentUser(
            username=username,
            scopes=payload.get("scopes", []),
            totp_enabled=True,  # For MVP — replace with real DB check later
        )
    except JWTError as e:
        logger.warning("JWT validation failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(token: str = Depends(oauth2_scheme)) -> CurrentUser:
    """FastAPI dependency to get authenticated user from JWT."""
    return decode_access_token(token)


# ──────────────────────────────────────────────────────────────────────────────
# TOTP (2FA) Utilities
# ──────────────────────────────────────────────────────────────────────────────


def generate_totp_secret() -> str:
    """Generate a new random base32 TOTP secret."""
    secret = pyotp.random_base32()
    logger.info("Generated new TOTP secret")
    return secret


def verify_totp(secret: str, code: str) -> bool:
    """
    Verify a TOTP code against the user's secret.

    Returns True if valid within current time step.
    """
    totp = pyotp.TOTP(
        secret,
        digits=auth_settings.totp_digits,
        interval=auth_settings.totp_interval_seconds,
    )
    valid = totp.verify(code.strip())
    if valid:
        logger.info("TOTP verification succeeded")
    else:
        logger.warning("TOTP verification failed")
    return valid


def get_totp_provisioning_uri(secret: str, username: str) -> str:
    """
    Generate otpauth:// URI for QR code scanning in authenticator apps.
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
