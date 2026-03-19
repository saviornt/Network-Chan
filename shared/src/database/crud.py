"""Async CRUD operations for Network-Chan database entities.

This module provides type-safe, reusable CRUD functions for core models.
All operations are asynchronous and use SQLAlchemy 2.0 async sessions.

Structured logging is used via shared.utils.logging_factory.get_logger.
"""

from typing import Optional, cast
from uuid import UUID

from sqlalchemy import delete, select, update
from sqlalchemy.engine import ResultProxy
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from shared.src.models.user_model import UserCreate, UserInDB, UserUpdate
from shared.src.models.faiss_models import (
    VectorMetadataCreate,
    VectorMetadataRead,
)
from shared.src.models.database_schema_models import (
    IncidentCreate,
    IncidentRead,
)
from shared.src.models.sqlite_models import Incident, User, FaissVectorMetadata
from shared.src.utils.logging_factory import get_logger


# ──────────────────────────────────────────────
#  Custom exceptions (logged with context)
# ──────────────────────────────────────────────


class EntityNotFoundError(Exception):
    """Raised when an entity is not found by lookup."""

    pass


class EntityAlreadyExistsError(Exception):
    """Raised when attempting to create a duplicate entity (unique constraint)."""

    pass


# ──────────────────────────────────────────────
#  User CRUD
# ──────────────────────────────────────────────


async def create_user(db: AsyncSession, user_in: UserCreate) -> UserInDB:
    """
    Create a new user in the database.

    Args:
        db: Active async database session
        user_in: Validated UserCreate schema (with plaintext password)

    Returns:
        UserInDB: Created user record (with DB-generated fields)

    Raises:
        EntityAlreadyExistsError: If username or email already exists
    """
    logger = get_logger(
        component="crud.user",
        operation="create_user",
        username=user_in.username,
    )

    db_user = User(
        username=user_in.username,
        email=user_in.email,
        hashed_password="",  # Must be hashed BEFORE calling this function
        role=user_in.role,
        is_active=True,
    )
    db.add(db_user)

    try:
        await db.commit()
        await db.refresh(db_user)
        logger.info("User created successfully", user_id=str(db_user.id))
        return UserInDB.model_validate(db_user)
    except IntegrityError as exc:
        await db.rollback()
        logger.warning(
            "User creation failed: duplicate constraint",
            error=str(exc),
            username=user_in.username,
            email=user_in.email,
        )
        raise EntityAlreadyExistsError("Username or email already exists") from exc
    except Exception as exc:
        await db.rollback()
        logger.exception(
            f"Unexpected error creating user: {exc}", username=user_in.username
        )
        raise


async def get_user_by_username(db: AsyncSession, username: str) -> Optional[UserInDB]:
    """
    Retrieve a user by their unique username.

    Args:
        db: Active async session
        username: Username to look up

    Returns:
        UserInDB | None: Found user or None if not found
    """
    logger = get_logger(
        component="crud.user", operation="get_by_username", username=username
    )

    stmt = select(User).where(User.username == username)
    result = await db.execute(stmt)
    db_user = result.scalar_one_or_none()

    if db_user:
        logger.debug("User found", user_id=str(db_user.id))
        return UserInDB.model_validate(db_user)
    else:
        logger.debug("User not found")
        return None


async def get_user_by_id(db: AsyncSession, user_id: UUID) -> Optional[UserInDB]:
    """
    Retrieve a user by their UUID primary key.

    Args:
        db: Active async session
        user_id: UUID of the user

    Returns:
        UserInDB | None
    """
    logger = get_logger(
        component="crud.user", operation="get_by_id", user_id=str(user_id)
    )

    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    db_user = result.scalar_one_or_none()

    if db_user:
        logger.debug("User found", username=db_user.username)
        return UserInDB.model_validate(db_user)
    else:
        logger.debug("User not found")
        return None


async def update_user(
    db: AsyncSession,
    user_id: UUID,
    user_update: UserUpdate,
) -> Optional[UserInDB]:
    """
    Partially update an existing user.

    Args:
        db: Active async session
        user_id: UUID of user to update
        user_update: Fields to update (partial)

    Returns:
        Updated UserInDB or None if user not found
    """
    logger = get_logger(
        component="crud.user",
        operation="update_user",
        user_id=str(user_id),
    )

    update_data = user_update.model_dump(exclude_unset=True)
    if not update_data:
        logger.debug("No fields to update")
        return await get_user_by_id(db, user_id)

    stmt = update(User).where(User.id == user_id).values(**update_data).returning(User)
    try:
        result = await db.execute(stmt)
        db_user = result.scalar_one_or_none()
        if db_user:
            await db.commit()
            await db.refresh(db_user)
            logger.info("User updated", changed_fields=list(update_data.keys()))
            return UserInDB.model_validate(db_user)
        else:
            logger.debug("User not found for update")
            return None
    except IntegrityError as exc:
        await db.rollback()
        logger.warning("Update failed: constraint violation", error=str(exc))
        raise EntityAlreadyExistsError(
            "Update would violate unique constraint"
        ) from exc


async def delete_user(db: AsyncSession, user_id: UUID) -> bool:
    """
    Hard-delete a user by ID (can be changed to soft-delete later).

    Args:
        db: Active session
        user_id: UUID to delete

    Returns:
        bool: True if deleted, False if not found
    """
    logger = get_logger(
        component="crud.user", operation="delete_user", user_id=str(user_id)
    )

    stmt = delete(User).where(User.id == user_id)
    result = await db.execute(stmt)

    proxy = cast(ResultProxy, result)
    deleted = proxy.rowcount > 0

    if deleted:
        await db.commit()
        logger.info("User deleted", user_id=str(user_id))
    else:
        logger.debug("User not found for deletion", user_id=str(user_id))

    return deleted


# ──────────────────────────────────────────────
#  Incident CRUD (minimal example — expand as needed)
# ──────────────────────────────────────────────


async def create_incident(
    db: AsyncSession, incident_in: IncidentCreate
) -> IncidentRead:
    """
    Create a new incident record.
    """
    logger = get_logger(
        component="crud.incident",
        operation="create",
        incident_type=incident_in.incident_type,
    )

    db_incident = Incident(**incident_in.model_dump())
    db.add(db_incident)
    await db.commit()
    await db.refresh(db_incident)

    logger.info("Incident created", incident_id=str(db_incident.id))
    return IncidentRead.model_validate(db_incident)


# ──────────────────────────────────────────────
#  FAISS Vector Metadata CRUD
# ──────────────────────────────────────────────


async def create_vector_metadata(
    db: AsyncSession,
    metadata_in: VectorMetadataCreate,
) -> VectorMetadataRead:
    """
    Create a new FAISS vector metadata record linking a vector ID to an entity.

    Args:
        db: Active async database session
        metadata_in: Validated metadata schema with vector_id already assigned

    Returns:
        VectorMetadataRead: Created metadata record

    Raises:
        EntityAlreadyExistsError: If vector_id already exists
    """
    logger = get_logger(
        component="crud.faiss_metadata",
        operation="create",
        vector_id=metadata_in.vector_id,
        entity_type=metadata_in.entity_type,
        entity_id=str(metadata_in.entity_id),
    )

    db_meta = FaissVectorMetadata(
        vector_id=metadata_in.vector_id,
        entity_type=metadata_in.entity_type,
        entity_id=metadata_in.entity_id,
        description=metadata_in.description,
        embedding_model=metadata_in.embedding_model,
        extra=metadata_in.extra,
    )

    db.add(db_meta)

    try:
        await db.commit()
        await db.refresh(db_meta)
        logger.info(
            "FAISS metadata created",
            metadata_id=str(db_meta.id),
            vector_id=db_meta.vector_id,
        )
        return VectorMetadataRead.model_validate(db_meta)
    except IntegrityError as exc:
        await db.rollback()
        logger.warning(
            "FAISS metadata creation failed: duplicate vector_id",
            error=str(exc),
            vector_id=metadata_in.vector_id,
        )
        raise EntityAlreadyExistsError("Vector ID already exists") from exc
    except Exception as exc:
        await db.rollback()
        logger.exception(f"Unexpected error creating FAISS metadata: {exc}")
        raise


async def get_vector_metadata_by_faiss_id(
    db: AsyncSession,
    vector_id: int,
) -> Optional[VectorMetadataRead]:
    """
    Retrieve FAISS vector metadata by its internal FAISS vector ID.

    Args:
        db: Active async session
        vector_id: FAISS-assigned vector ID

    Returns:
        VectorMetadataRead | None: Found metadata or None
    """
    logger = get_logger(
        component="crud.faiss_metadata",
        operation="get_by_vector_id",
        vector_id=vector_id,
    )

    stmt = select(FaissVectorMetadata).where(FaissVectorMetadata.vector_id == vector_id)
    result = await db.execute(stmt)
    db_meta = result.scalar_one_or_none()

    if db_meta:
        logger.debug("FAISS metadata found", metadata_id=str(db_meta.id))
        return VectorMetadataRead.model_validate(db_meta)
    else:
        logger.debug("FAISS metadata not found", vector_id=vector_id)
        return None


# ──────────────────────────────────────────────
#  Exports
# ──────────────────────────────────────────────

__all__ = [
    "create_user",
    "get_user_by_username",
    "get_user_by_id",
    "update_user",
    "delete_user",
    "create_incident",
    "EntityNotFoundError",
    "EntityAlreadyExistsError",
    "create_vector_metadata",
    "get_vector_metadata_by_faiss_id",
]
