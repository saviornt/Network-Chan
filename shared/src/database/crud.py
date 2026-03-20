"""Generic base class for modular, type-safe async CRUD operations.

Reduces duplication across entities while preserving project standards.
"""

from typing import Generic, TypeVar, Type, Optional, Sequence
from uuid import UUID

from sqlalchemy import select, update, delete
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from shared.src.utils.logging_factory import get_logger

TModel = TypeVar("TModel")
TCreate = TypeVar("TCreate")
TRead = TypeVar("TRead")
TUpdate = TypeVar("TUpdate")


class BaseCRUD(Generic[TModel, TCreate, TRead, TUpdate]):
    """Base repository providing standard CRUD with async support.

    Subclass for each entity and add custom methods as needed.

    Example:
        class UserCRUD(BaseCRUD[User, UserCreate, UserInDB, UserUpdate]):
            async def get_by_username(...): ...
    """

    def __init__(self, model: Type[TModel]):
        self.model = model
        self.logger = get_logger(component=f"crud.{model.__name__.lower()}")

    async def create(self, db: AsyncSession, obj_in: TCreate) -> TRead:
        """Create a new record and return the read model."""
        db_obj = self.model(**obj_in.model_dump())
        db.add(db_obj)
        try:
            await db.commit()
            await db.refresh(db_obj)
            self.logger.info("Created", id=getattr(db_obj, "id", None))
            return TRead.model_validate(db_obj)  # type: ignore
        except IntegrityError as e:
            await db.rollback()
            self.logger.warning("Duplicate constraint", error=str(e))
            raise EntityAlreadyExistsError from e

    async def get(self, db: AsyncSession, id: UUID) -> Optional[TRead]:
        """Get by primary key (UUID)."""
        stmt = select(self.model).where(self.model.id == id)
        result = await db.execute(stmt)
        obj = result.scalar_one_or_none()
        return TRead.model_validate(obj) if obj else None

    async def get_multi(
        self, db: AsyncSession, skip: int = 0, limit: int = 100
    ) -> Sequence[TRead]:
        """Paginated list retrieval."""
        stmt = select(self.model).offset(skip).limit(limit)
        result = await db.execute(stmt)
        return [TRead.model_validate(o) for o in result.scalars().all()]

    async def update(
        self, db: AsyncSession, id: UUID, obj_in: TUpdate
    ) -> Optional[TRead]:
        """Partial update by ID."""
        update_data = obj_in.model_dump(exclude_unset=True)
        if not update_data:
            return await self.get(db, id)

        stmt = (
            update(self.model)
            .where(self.model.id == id)
            .values(**update_data)
            .returning(self.model)
        )
        result = await db.execute(stmt)
        db_obj = result.scalar_one_or_none()
        if db_obj:
            await db.commit()
            await db.refresh(db_obj)
            self.logger.info("Updated", id=id)
            return TRead.model_validate(db_obj)
        return None

    async def delete(self, db: AsyncSession, id: UUID) -> bool:
        """Delete by ID."""
        stmt = delete(self.model).where(self.model.id == id)
        result = await db.execute(stmt)
        deleted = result.rowcount > 0
        if deleted:
            await db.commit()
            self.logger.info("Deleted", id=id)
        return deleted

    # TODO: Add soft-delete support, filtering, ordering, count, exists checks
