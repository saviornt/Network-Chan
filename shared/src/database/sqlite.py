"""Database utilities for Network-Chan (SQLite via SQLAlchemy async)."""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from shared.src.config.shared_settings import shared_settings
from shared.src.models.user_model import UserBase  # Import all models for metadata


def get_async_engine(db_path: str):
    """Create async SQLAlchemy engine for SQLite."""
    # SQLite async URL format
    return create_async_engine(f"sqlite+aiosqlite:///{db_path}", echo=False)


def get_async_session(db_path: str):
    """Session factory for async operations."""
    engine = get_async_engine(db_path)
    return sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency: provides an async SQLAlchemy session.

    Usage in routes:
        async def some_route(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with get_async_session(shared_settings.full_db_path) as session:
        yield session
