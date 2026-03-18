"""Pydantic models for user authentication, registration, and TOTP flows.

Supports the bootstrap admin → user registration → enforced TOTP login pattern.
All models use strict validation; passwords are never stored plaintext.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import EmailStr, Field, field_validator

from .base_model import NetworkChanBaseModel  # Assuming you have the common base


class UserBase(NetworkChanBaseModel):
    """Common base fields for all user-related models."""

    username: str = Field(
        min_length=3,
        max_length=32,
        pattern=r"^[a-zA-Z0-9_-]+$",
        description="Alphanumeric username (letters, numbers, _, -)",
    )


class UserCreate(UserBase):
    """Input model for creating a new user (registration)."""

    password: str = Field(
        min_length=12,
        max_length=128,
        description="Plaintext password (will be hashed before storage)",
    )
    email: EmailStr | None = Field(
        default=None, description="Optional email for recovery/notifications"
    )
    totp_secret: str | None = Field(
        default=None,
        description="Base32 TOTP secret (generated during registration)",
    )
    totp_uri: str | None = Field(
        default=None,
        description="otpauth:// URI for QR code (only returned once during setup)",
    )

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if len(v) < 12:
            raise ValueError("Password must be at least 12 characters")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in v):
            raise ValueError("Password must contain at least one special character")
        return v


class BootstrapAdminCreate(NetworkChanBaseModel):
    """Special model for first-time bootstrap admin (no TOTP, random password)."""

    username: Literal["admin"] = Field(default="admin")
    password: str = Field(
        min_length=12,
        max_length=128,
        description="Randomly generated 12+ char password (shown only once)",
    )


class UserInDB(UserBase):
    """Internal storage model (what actually goes in SQLite / DB)."""

    model_config = {"frozen": False}  # Allow updates (e.g. password change)

    hashed_password: str = Field(
        description="bcrypt hashed password (never return this!)"
    )
    totp_secret: str | None = Field(
        default=None,
        description="Base32 secret for TOTP (encrypted in production)",
    )
    is_bootstrap: bool = Field(
        default=False,
        description="True only for the initial admin account",
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: datetime | None = None
    failed_login_attempts: int = Field(default=0, ge=0)
    locked_until: datetime | None = None


class UserLogin(NetworkChanBaseModel):
    """Input for standard login (dashboard / appliance config page)."""

    username: str = Field(min_length=3, max_length=32)
    password: str = Field(min_length=1)
    totp_code: str | None = Field(
        default=None,
        pattern=r"^\d{6}$",
        description="6-digit TOTP code (required after registration)",
    )


class UserLoginResponse(NetworkChanBaseModel):
    """Safe response after successful authentication."""

    access_token: str = Field(description="JWT / session token")
    token_type: Literal["bearer"] = "bearer"
    user: UserBase
    requires_totp_setup: bool = Field(
        default=False,
        description="True only during first login after registration",
    )


class TOTPSetup(NetworkChanBaseModel):
    """Response when user needs to configure TOTP (QR + secret)."""

    totp_uri: str = Field(description="otpauth:// URI → QR code")
    secret: str = Field(description="Base32 secret (backup)")
    # In real code: generate QR image server-side or client-side from URI
