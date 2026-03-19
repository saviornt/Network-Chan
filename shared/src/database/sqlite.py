"""Enhanced async SQLite database utilities for Network-Chan.

This module provides a singleton-style async engine and session factory
using SQLAlchemy 2.0, configured via Pydantic Settings.

It handles connection pooling, WAL mode, health checks, and automatic
table creation on first use.
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.exc import SQLAlchemyError

from shared.src.settings.sqlite_settings import sqlite_settings
from shared.src.models.sqlite_models import Base  # Import all models

logger = logging.getLogger(__name__)

# Global singletons (initialized lazily)
_engine: Optional[AsyncEngine] = None
_session_factory: Optional[async_sessionmaker[AsyncSession]] = None


def get_async_engine() -> AsyncEngine:
    """
    Returns (and lazily creates) the shared async SQLAlchemy engine.

    Always uses WAL mode and settings from SQLiteSettings.

    Returns:
        AsyncEngine: Configured engine instance
    """
    global _engine
    if _engine is None:
        url = f"sqlite+aiosqlite:///{sqlite_settings.full_db_path}"
        _engine = create_async_engine(
            url,
            echo=sqlite_settings.echo,
            connect_args={"pragma": "journal_mode=WAL"},
            pool_size=sqlite_settings.pool_size,
            max_overflow=0,  # fixed pool size — predictable memory on Pi
            pool_timeout=sqlite_settings.pool_timeout,
            pool_pre_ping=sqlite_settings.pool_pre_ping,
        )
        logger.info("Async SQLite engine initialized: %s", url)
    return _engine


def get_async_session_factory() -> async_sessionmaker[AsyncSession]:
    """
    Returns the async session factory bound to the shared engine.

    Returns:
        async_sessionmaker: Factory for creating AsyncSession instances
    """
    global _session_factory
    if _session_factory is None:
        engine = get_async_engine()
        _session_factory = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )
    return _session_factory


@asynccontextmanager
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency: yields an async SQLAlchemy session.

    Automatically commits on success, rolls back on exception.

    Usage:
        async def route(db: AsyncSession = Depends(get_db)):
            ...

    Yields:
        AsyncSession: Database session
    """
    session_factory = get_async_session_factory()
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_database() -> None:
    """
    Create all tables defined in Base.metadata if they do not exist.

    Should be called once during application startup (e.g. in lifespan).
    Safe to call multiple times — does nothing if tables already exist.
    """
    engine = get_async_engine()
    try:
        async with engine.begin() as conn:
            # Run synchronous metadata.create_all in async context
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables initialized/verified")
    except SQLAlchemyError as e:
        logger.error("Failed to initialize database tables: %s", e)
        raise


async def check_db_health(session: AsyncSession) -> bool:
    """
    Verify basic database connectivity and write capability.

    Performs a simple SELECT 1 and a WAL checkpoint.

    Args:
        session: Active async session

    Returns:
        bool: True if database responds and WAL checkpoint succeeds
    """
    try:
        await session.execute(text("SELECT 1"))
        # Test write capability via WAL checkpoint
        result = await session.execute(text("PRAGMA wal_checkpoint(FULL);"))
        checkpoint_info = result.fetchone()
        if checkpoint_info and checkpoint_info[0] == 0:  # busy=0 → success
            return True
        return False
    except SQLAlchemyError as e:
        logger.warning("Database health check failed: %s", e)
        return False


async def shutdown_database() -> None:
    """
    Gracefully shut down the database engine on application exit.

    Releases all pooled connections and cleans up resources.
    Should be called in FastAPI shutdown event or atexit handler.
    """
    global _engine, _session_factory
    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _session_factory = None
        logger.info("Async SQLite engine disposed")
