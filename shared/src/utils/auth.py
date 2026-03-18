"""Shared authentication utilities for Network-Chan.

Provides JWT encoding/decoding, TOTP generation/verification, and FastAPI dependencies.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

import pyotp
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

from shared.src.config.auth_settings import auth_settings
from shared.src.models.auth_model import TokenResponse, CurrentUser
from shared.src.utils.logging_factory import get_logger

logger = get_logger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")  # Update path as needed


def create_access_token(
    username: str,
    scopes: list[str] | None = None,
    expires_delta: timedelta | None = None,
) -> TokenResponse:
    """
    Generate a new JWT access token (and optional refresh token).
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
    """
    try:
        payload = jwt.decode(
            token,
            auth_settings.jwt_secret.get_secret_value(),
            algorithms=[auth_settings.jwt_algorithm],
        )
        username: str = payload.get("sub")
        if username is None:
            raise JWTError("Missing subject")
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
