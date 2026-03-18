from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from shared.src.config.auth_settings import auth_settings
from shared.src.models.auth_model import LoginRequest, TokenResponse, TotpSetupResponse
from shared.src.services.auth_service import verify_login, change_password, enable_totp
from shared.src.utils.auth import create_access_token, get_totp_provisioning_uri
from shared.src.utils.database import get_db

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    user = await verify_login(db, request.username, request.password, request.totp_code)
    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credentials")

    token = create_access_token(user.username)
    return token


@router.post("/change-credentials")
async def change_credentials(
    old_password: str,
    new_password: str,
    new_username: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    # Verify old password
    success = await change_password(db, current_user.username, old_password, new_password)
    if not success:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid old password")

    # Validate new password strength
    is_valid, feedback = password_validator.validate(
        new_password,
        username=new_username or current_user.username,
        user_data=[]  # Add email/phone if you have them
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

    # If this is first login, force TOTP setup next
    user = await get_user_by_username(db, current_user.username)
    if user and not user.totp_enabled:
        return {"message": "Password updated", "next_step": "setup_totp"}

    return {"message": "Credentials updated successfully"}


@router.get("/totp-setup", response_model=TotpSetupResponse)
async def totp_setup(current_user: CurrentUser = Depends(get_current_user)):
    secret = generate_totp_secret()
    uri = get_totp_provisioning_uri(secret, current_user.username)
    return TotpSetupResponse(secret=secret, provisioning_uri=uri)