"""Pydantic models for authentication payloads, tokens, and related data.

These models define request/response shapes for login, token validation,
TOTP setup, and current user info. No ORM or FAISS storage is required here —
auth flows are transient or JWT-based.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class LoginRequest(BaseModel):
    """Request body for user login (username + password + optional TOTP code)."""

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        validate_default=True,
        validate_assignment=True,
    )

    username: str = Field(
        ...,
        min_length=3,
        description="Username for authentication",
    )
    password: str = Field(
        ...,
        min_length=8,
        description="Plaintext password (will be hashed server-side)",
    )
    totp_code: Optional[str] = Field(
        default=None,
        pattern=r"^\d{6,8}$",
        description="6–8 digit TOTP code if 2FA is enabled for this user",
    )


class TokenResponse(BaseModel):
    """Successful login response containing JWT access token (and optional refresh)."""

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    access_token: str = Field(
        ...,
        description="JWT bearer token for subsequent requests",
    )
    token_type: str = Field(
        default="bearer",
        description="Token type (usually 'bearer')",
    )
    expires_in: int = Field(
        ...,
        ge=60,
        description="Expiration time in seconds",
    )
    refresh_token: Optional[str] = Field(
        default=None,
        description="Refresh token (if refresh token rotation is implemented)",
    )


class TokenData(BaseModel):
    """Decoded JWT payload / authenticated user claims.

    Used internally after token validation.
    """

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    sub: str = Field(
        ...,
        description="Subject — usually username or user ID string",
    )
    exp: datetime = Field(
        ...,
        description="Expiration timestamp (UTC)",
    )
    scopes: list[str] = Field(
        default_factory=list,
        description="Granted permissions/scopes (e.g. ['read:telemetry', 'write:policy'])",
    )


class TotpSetupResponse(BaseModel):
    """Response when setting up TOTP for the first time."""

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    secret: str = Field(
        ...,
        description="Base32-encoded TOTP secret (for manual entry)",
    )
    provisioning_uri: str = Field(
        ...,
        description="otpauth:// URI for scanning into authenticator app",
    )
    qr_code_url: Optional[str] = Field(
        default=None,
        description="URL to a QR code image (if generated server-side)",
    )


class CurrentUser(BaseModel):
    """Representation of the authenticated user (returned after token validation).

    Used in dependency injection (e.g. get_current_user) and profile endpoints.
    """

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    username: str = Field(..., description="Authenticated username")

    # TODO:Replace with RBAC later
    is_admin: bool = Field(
        default=True,
        description="For MVP: assume single admin user (later replace with RBAC)",
    )

    scopes: list[str] = Field(
        default_factory=list,
        description="Active permissions/scopes",
    )
    totp_enabled: bool = Field(
        default=False,
        description="Whether two-factor authentication is active",
    )


__all__ = [
    "LoginRequest",
    "TokenResponse",
    "TokenData",
    "TotpSetupResponse",
    "CurrentUser",
]
