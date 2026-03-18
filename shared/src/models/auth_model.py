"""Pydantic models for authentication payloads, tokens, and related data.

These models are used for login requests/responses, token validation, and 2FA flows.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from shared.src.utils.auth import TokenData  # We'll create this later


class LoginRequest(BaseModel):
    """
    Request body for admin login (username + password + optional TOTP code).
    """

    username: str = Field(..., min_length=3)
    password: str = Field(..., min_length=8)
    totp_code: Optional[str] = Field(
        default=None,
        description="6-8 digit TOTP code if 2FA is enabled for this user",
    )


class TokenResponse(BaseModel):
    """
    Successful login response containing JWT access token (and optional refresh).
    """

    access_token: str = Field(..., description="JWT bearer token")
    token_type: str = Field(default="bearer")
    expires_in: int = Field(..., description="Expiration in seconds")
    refresh_token: Optional[str] = Field(
        default=None,
        description="Refresh token (if implemented)",
    )


class TotpSetupResponse(BaseModel):
    """
    Response when setting up TOTP for the first time.
    """

    secret: str = Field(..., description="Base32-encoded TOTP secret")
    provisioning_uri: str = Field(
        ..., description="otpauth:// URI for scanning into authenticator app"
    )
    qr_code_url: Optional[str] = Field(
        default=None,
        description="URL to a QR code image (if generated server-side)",
    )


class CurrentUser(BaseModel):
    """
    Representation of the authenticated user (returned from token validation).
    """

    username: str
    is_admin: bool = Field(default=True)  # For MVP, assume single admin user
    scopes: list[str] = Field(default_factory=list)
    totp_enabled: bool = Field(default=False)
