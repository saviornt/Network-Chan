"""Dynamic CRUD operations for SQLite using aiosqlite.

All functions accept table name and use parameterized queries to prevent SQL injection.
Dynamic SQL is built safely via placeholders, never raw f-strings for values.
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

from .sqlite import get_db


async def create_record(table: str, data: Dict[str, Any]) -> int:
    """Insert a record into the specified table and return the new rowid.

    Args:
        table: Table name (must be valid/escaped identifier).
        data: Column names → values dictionary.

    Returns:
        The rowid of the inserted record.
    """
    if not data:
        raise ValueError("Data dictionary cannot be empty")

    columns = list(data.keys())
    placeholders = ", ".join("?" for _ in columns)
    values = tuple(data[col] for col in columns)

    sql = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})"

    async with get_db() as conn:
        cursor = await conn.execute(sql, values)
        return cursor.lastrowid


async def read_records(
    table: str,
    where: str | None = None,
    params: Tuple | Dict[str, Any] | None = None,
    limit: int | None = None,
) -> List[Dict[str, Any]]:
    """Fetch records from a table with optional WHERE clause and limit.

    Args:
        table: Table name.
        where: Optional WHERE clause (without 'WHERE' keyword).
        params: Parameters for the WHERE clause (tuple or dict).
        limit: Optional row limit.

    Returns:
        List of records as dictionaries.
    """
    sql = f"SELECT * FROM {table}"
    if where:
        sql += f" WHERE {where}"
    if limit is not None:
        sql += " LIMIT ?"
        params = params or ()
        if isinstance(params, dict):
            raise ValueError("Dict params not supported with limit")
        params = (*params, limit)
    elif params is None:
        params = ()

    async with get_db() as conn:
        cursor = await conn.execute(sql, params)
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


# Similar implementations for update_record, delete_record...
# (add as needed; keep parameterized!)
