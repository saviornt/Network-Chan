from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from shared.src.models.user_model import UserInDB, hash_password, verify_password
from shared.src.utils.auth import generate_totp_secret, verify_totp


async def get_user_by_username(db: AsyncSession, username: str) -> Optional[UserInDB]:
    result = await db.execute(select(UserInDB).where(UserInDB.username == username))
    return result.scalar_one_or_none()


async def create_initial_admin(db: AsyncSession):
    """Run once on first startup if no users exist."""
    existing = await get_user_by_username(db, auth_settings.default_admin_username)
    if existing:
        return

    user = UserInDB(
        username=auth_settings.default_admin_username,
        hashed_password=auth_settings.default_admin_password_hash,
        totp_secret=None,
        totp_enabled=False,
        created_at=datetime.utcnow(),
    )
    db.add(user)
    await db.commit()


async def change_password(
    db: AsyncSession, username: str, old_password: str, new_password: str
) -> bool:
    user = await get_user_by_username(db, username)
    if not user or not verify_password(old_password, user.hashed_password):
        return False

    user.hashed_password = hash_password(new_password)
    await db.commit()
    return True


async def enable_totp(db: AsyncSession, username: str, code: str) -> bool:
    user = await get_user_by_username(db, username)
    if not user:
        return False

    if user.totp_secret is None:
        # First time — generate secret
        secret = generate_totp_secret()
        if verify_totp(secret, code):
            user.totp_secret = secret
            user.totp_enabled = True
            await db.commit()
            return True
        return False

    # Already set — just verify
    return verify_totp(user.totp_secret, code)


async def verify_login(
    db: AsyncSession, username: str, password: str, totp_code: Optional[str] = None
) -> Optional[UserInDB]:
    user = await get_user_by_username(db, username)
    if not user or not verify_password(password, user.hashed_password):
        return None

    if user.totp_enabled:
        if not totp_code or not verify_totp(user.totp_secret, totp_code):
            return None

    user.last_login = datetime.utcnow()
    await db.commit()
    return user
