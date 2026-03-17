"""Database session and connection management.

Provides async context managers for SQLite connections (aiosqlite).
Later extensible to PostgreSQL/asyncpg or other backends.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

import aiosqlite

from shared.src.config.settings import settings


@asynccontextmanager
async def get_db() -> AsyncGenerator[aiosqlite.Connection, None]:
    """Async context manager for aiosqlite connection.

    Yields a connection that is auto-committed on success, rolled back on exception.
    Path comes from settings.full_db_path.
    """
    db_path = str(settings.full_db_path)
    async with aiosqlite.connect(db_path) as conn:
        conn.row_factory = aiosqlite.Row  # Enables dict-like row access
        try:
            yield conn
            await conn.commit()
        except Exception:
            await conn.rollback()
            raise
