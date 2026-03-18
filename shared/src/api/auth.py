"""FastAPI authentication endpoints for Network-Chan.

Handles login, credential changes, and TOTP setup/verification.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from shared.src.models.auth_model import (
    LoginRequest,
    TokenResponse,
    TotpSetupResponse,
    CurrentUser,
)
from shared.src.services.auth_service import (
    login_user,
    change_password,
    get_user_by_username,
)
from shared.src.utils.auth import (
    get_totp_provisioning_uri,
    password_validator,
    get_current_user,
    generate_totp_secret,
)
from shared.src.database.sqlite import get_db

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    """
    Authenticate user and return JWT access token.

    For initial login: username + password only
    After 2FA setup: username + password + totp_code required
    """
    token, errors = await login_user(
        db=db,
        username=request.username,
        password=request.password,
        totp_code=request.totp_code,
    )

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=errors or "Authentication failed",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return token


@router.post("/change-credentials")
async def change_credentials(
    old_password: str,
    new_password: str,
    new_username: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Change user password (required) and optionally username.
    Validates new password strength.
    """
    success = await change_password(
        db=db,
        username=current_user.username,
        old_password=old_password,
        new_password=new_password,
    )
    if not success:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid old password")

    # Validate new password strength
    is_valid, feedback = password_validator.validate(
        new_password,
        username=new_username or current_user.username,
        user_data=[],  # Add email/phone if you have them
    )

    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password is too weak",
            headers={"X-Password-Feedback": "; ".join(feedback)},
        )

    # Optional username change
    if new_username and new_username != current_user.username:
        # TODO: update username in DB
        pass

    # If this is first login, force TOTP setup next
    user = await get_user_by_username(db, current_user.username)
    if user and not user.totp_enabled:
        return {"message": "Password updated", "next_step": "setup_totp"}

    return {"message": "Credentials updated successfully"}


@router.get("/totp-setup", response_model=TotpSetupResponse)
async def totp_setup(current_user: CurrentUser = Depends(get_current_user)):
    """
    Generate TOTP secret and provisioning URI for QR code scanning.
    """
    secret = generate_totp_secret()
    uri = get_totp_provisioning_uri(secret, current_user.username)
    return TotpSetupResponse(secret=secret, provisioning_uri=uri)
