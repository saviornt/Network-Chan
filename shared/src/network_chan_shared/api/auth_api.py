"""FastAPI authentication endpoints for Network-Chan.

Handles login, password changes, and TOTP (2FA) setup/verification.
All endpoints are async and use dependency injection for DB sessions and current user.

Security notes:
- Passwords are hashed with Argon2id (memory-hard, NIST/NSA preferred)
- JWT tokens are short-lived with optional refresh support (TODO)
- TOTP is enforced after initial setup — required for subsequent logins
- Username changes are disabled for MVP (can be re-enabled later with alias support)
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import (
    LoginRequest,
    TokenResponse,
    TotpSetupResponse,
    CurrentUser,
)
from ..authentication import (
    login_user,
    change_password,
    get_user_by_username,
)
from ..authentication.auth import (
    get_totp_provisioning_uri,
    password_validator,
    get_current_user,
    generate_totp_secret,
)
from ..database.sqlite import get_db
from ..utils.logging_factory import get_logger


logger = get_logger("auth", category="api")

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Authenticate user and issue JWT access token.

    Login flow:
    - Initial/first login: username + password only
    - After TOTP setup: username + password + totp_code required

    Args:
        request: Login credentials (username, password, optional TOTP code)
        db: Injected async database session

    Returns:
        TokenResponse with access_token and expiration info

    Raises:
        HTTPException 401: Invalid credentials or TOTP
        HTTPException 400: Malformed request
    """
    token, errors = await login_user(
        db=db,
        username=request.username,
        password=request.password,
        totp_code=request.totp_code,
    )

    if not token:
        logger.warning(
            "Login attempt failed",
            username=request.username,
            errors=errors,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=errors or "Authentication failed",
            headers={"WWW-Authenticate": "Bearer"},
        )

    logger.info(
        "User logged in successfully",
        username=request.username,
        totp_used=bool(request.totp_code),
    )
    return token


@router.post("/change-credentials")
async def change_credentials(
    old_password: str,
    new_password: str,
    new_username: Optional[str] = None,  # Disabled for MVP; alias support later
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> dict:
    """Change the authenticated user's password (and optionally username in future).

    Requirements:
    - Old password must match
    - New password must pass strength validation (NIST/zxcvbn)
    - Username change is disabled for MVP (TODO: add alias support)

    Args:
        old_password: Current password for verification
        new_password: Desired new password
        new_username: Optional new username (ignored for now)
        db: Injected async DB session
        current_user: Authenticated user (from JWT dependency)

    Returns:
        Dict with success message and optional next_step

    Raises:
        HTTPException 400: Invalid old password or weak new password
        HTTPException 403: Username change attempted (MVP restriction)
    """
    if new_username and new_username != current_user.username:
        logger.warning(
            "Username change attempted but disabled in MVP",
            current=current_user.username,
            attempted=new_username,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Username changes are not supported yet (MVP limitation)",
        )

    success = await change_password(
        db=db,
        username=current_user.username,
        old_password=old_password,
        new_password=new_password,
    )

    if not success:
        logger.warning(
            "Password change failed – invalid old password",
            username=current_user.username,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid old password",
        )

    # Validate new password strength
    is_valid, feedback = password_validator.validate(
        new_password,
        username=current_user.username,
        user_data=[],  # TODO: add email/phone if stored
    )

    if not is_valid:
        logger.warning(
            "New password rejected – too weak",
            username=current_user.username,
            feedback=feedback,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password is too weak: " + "; ".join(feedback),
            headers={"X-Password-Feedback": "; ".join(feedback)},
        )

    # Check if this is first login (force TOTP setup)
    user = await get_user_by_username(db, current_user.username)
    if user and not user.totp_enabled:
        logger.info(
            "Password changed; forcing TOTP setup on next login",
            username=current_user.username,
        )
        return {"message": "Password updated successfully", "next_step": "setup_totp"}

    logger.info(
        "Credentials updated successfully",
        username=current_user.username,
    )
    return {"message": "Credentials updated successfully"}


@router.get("/totp-setup", response_model=TotpSetupResponse)
async def totp_setup(
    current_user: CurrentUser = Depends(get_current_user),
) -> TotpSetupResponse:
    """Generate TOTP secret and provisioning URI for QR code scanning.

    This endpoint is called during onboarding or when enabling 2FA.
    The returned URI can be scanned by authenticator apps (Google Authenticator, etc.).

    Args:
        current_user: Authenticated user (from JWT dependency)

    Returns:
        TotpSetupResponse with secret and otpauth:// URI

    Raises:
        HTTPException 403: If TOTP is already enabled (prevent overwrite)
    """
    # TODO: Check if TOTP is already enabled → reject or return current setup
    # For MVP we allow re-generation (user can revoke old secret manually)

    secret = generate_totp_secret()
    uri = get_totp_provisioning_uri(secret, current_user.username)

    logger.info(
        "TOTP setup requested",
        username=current_user.username,
    )

    return TotpSetupResponse(
        secret=secret,
        provisioning_uri=uri,
        # qr_code_url=...  # TODO: optional server-side QR generation
    )


# Future endpoints (stubs for later sprints)
# @router.post("/totp-verify")
# async def verify_totp_setup(...):
#     """Verify TOTP code during initial setup."""
#     # TODO: implement verification + DB update

# @router.post("/logout")
# async def logout(...):
#     """Invalidate current session / refresh token."""
#     # TODO: implement token blacklisting or short expiry

# Public API exports (none needed — router is included via api/__init__.py)
