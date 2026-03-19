"""Authentication business logic service for Network-Chan.

This module handles user verification, credential changes, TOTP setup,
and token generation. It interacts with the database via SQLAlchemy async
engine (backed by aiosqlite) and uses low-level auth utilities from auth.py.

All functions are async to support non-blocking I/O.
"""

from datetime import datetime, timezone
from typing import List, Optional, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.src.settings.auth_settings import auth_settings
from shared.src.models.auth_model import TokenResponse
from shared.src.models.user_model import UserInDB
from shared.src.authentication.auth import (
    generate_totp_secret,
    verify_totp,
    create_access_token,
    hash_password,
    verify_password,
)
from shared.src.utils.logging_factory import get_logger

logger = get_logger(__name__)


async def get_user_by_username(
    db: AsyncSession,
    username: str,
) -> Optional[UserInDB]:
    """
    Retrieve a user by username from the database.

    Args:
        db: Active async SQLAlchemy session
        username: Username to look up

    Returns:
        UserInDB object if found, None otherwise
    """
    result = await db.execute(select(UserInDB).filter_by(username=username))
    return result.scalar_one_or_none()


async def create_initial_admin(db: AsyncSession) -> None:
    """
    Create the initial admin user if no users exist in the database.

    Uses default credentials from auth_settings.
    Should be called once on first startup (e.g. in startup event).
    """
    existing = await get_user_by_username(db, auth_settings.default_admin_username)
    if existing:
        logger.debug("Initial admin already exists – skipping creation")
        return

    default_hash = auth_settings.default_admin_password_hash
    if not default_hash:
        logger.warning(
            "No default admin password hash set in config – "
            "initial admin creation skipped"
        )
        return

    # Create default admin user representation (for seeding or fallback)
    user = UserInDB(
        id=None,  # Auto-generated UUID by DB on insert
        username=auth_settings.default_admin_username,
        email=None,  # Optional; can be set later via update
        role="admin",  # Explicit admin role for this default user
        hashed_password=default_hash,
        totp_secret=None,
        totp_enabled=False,
        is_active=True,  # Account is enabled by default
        last_login=None,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(
            timezone.utc
        ),  # Usually set by DB trigger, but safe to include
    )

    db.add(user)
    await db.commit()
    await db.refresh(user)

    logger.info(
        "Initial admin user created",
        username=user.username,
    )


async def change_password(
    db: AsyncSession,
    username: str,
    old_password: str,
    new_password: str,
) -> bool:
    """
    Change the user's password after verifying the old one.

    Args:
        db: Active async SQLAlchemy session
        username: Username to update
        old_password: Current plaintext password
        new_password: New plaintext password

    Returns:
        bool: True if change succeeded, False if old password invalid
    """
    user = await get_user_by_username(db, username)
    if not user or not verify_password(old_password, user.hashed_password):
        logger.warning(
            "Password change failed – invalid old password", username=username
        )
        return False

    user.hashed_password = hash_password(new_password)
    await db.commit()
    await db.refresh(user)

    logger.info("Password changed successfully", username=username)
    return True


async def enable_totp(
    db: AsyncSession,
    username: str,
    code: str,
) -> bool:
    """
    Enable or verify TOTP for a user by checking the provided code.

    Behavior:
    - If no TOTP secret exists yet (first setup): generate one and verify the code.
    - If secret already exists: verify the code against it.
    - TOTP is treated as **required** after initial setup — this function enforces verification.

    Args:
        db: Active async SQLAlchemy session
        username: Username to enable/verify TOTP for
        code: Current TOTP code from authenticator app

    Returns:
        bool: True if setup or verification succeeded, False otherwise

    Raises:
        ValueError: If called with invalid user or missing secret on non-first call
    """
    user = await get_user_by_username(db, username)
    if not user:
        logger.warning(
            "TOTP enable/verification failed – user not found", username=username
        )
        return False

    if user.totp_secret is None:
        # First-time setup: generate secret and verify the provided code
        secret = generate_totp_secret()
        if not verify_totp(secret, code):
            logger.warning(
                "First-time TOTP setup failed – invalid code", username=username
            )
            return False

        user.totp_secret = secret
        user.totp_enabled = True
        await db.commit()
        await db.refresh(user)

        logger.info("TOTP successfully enabled (first setup)", username=username)
        return True

    else:
        # Subsequent verification: must match existing secret
        if not verify_totp(user.totp_secret, code):
            logger.warning("TOTP verification failed – invalid code", username=username)
            return False

        # No change needed to DB (already enabled)
        logger.debug("TOTP verification succeeded (already enabled)", username=username)
        return True


async def verify_login(
    db: AsyncSession,
    username: str,
    password: str,
    totp_code: Optional[str] = None,
) -> Tuple[Optional[UserInDB], List[str]]:
    """
    Verify username/password and optional TOTP code.

    Args:
        db: Active async SQLAlchemy session
        username: Provided username
        password: Provided plaintext password
        totp_code: Optional 6-8 digit TOTP code

    Returns:
        Tuple[Optional[UserInDB], List[str]]:
            - User object if authentication succeeds, None otherwise
            - List of error messages (empty on success)
    """
    errors: List[str] = []

    user = await get_user_by_username(db, username)
    if not user:
        errors.append("Invalid username or password")
        return None, errors

    if not verify_password(password, user.hashed_password):
        errors.append("Invalid username or password")
        return None, errors

    if user.totp_enabled:
        if not totp_code:
            errors.append("TOTP code required")
            return None, errors

        secret = user.totp_secret
        if secret is None or not verify_totp(secret, totp_code):
            errors.append("Invalid TOTP code")
            return None, errors

    user.last_login = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(user)

    logger.info("Successful login", username=username)
    return user, []


async def login_user(
    db: AsyncSession,
    username: str,
    password: str,
    totp_code: Optional[str] = None,
) -> Tuple[Optional[TokenResponse], List[str]]:
    """
    Full login flow: verify credentials → issue JWT.

    Returns (TokenResponse or None, list of errors).
    """
    user, errors = await verify_login(db, username, password, totp_code)
    if not user:
        return None, errors

    token = create_access_token(user.username)
    return token, []
