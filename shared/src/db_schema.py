# shared/src/db_schema.py

from typing import Optional
import sqlite3
import asyncio
# from numba import jit  # For potential perf in queries (stub)

#@jit(nopython=True)
def mock_compute_embedding(vector: list[float]) -> float:  # Numba stub for future vector ops
    return sum(vector)  # Placeholder math

async def create_tables(conn: sqlite3.Connection) -> None:
    cursor = conn.cursor()
    await asyncio.sleep(0)  # Async yield stub for concurrency
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS incidents (
            id INTEGER PRIMARY KEY,
            timestamp TEXT NOT NULL,
            description TEXT,
            vector_id TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS models (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            version TEXT,
            quantized BLOB
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS audits (
            id INTEGER PRIMARY KEY,
            action TEXT NOT NULL,
            approved INTEGER
        )
    ''')
    conn.commit()

async def init_db(db_path: str = 'network_chan.db') -> None:
    conn: Optional[sqlite3.Connection] = None
    try:
        conn = sqlite3.connect(db_path)
        await create_tables(conn)
    finally:
        if conn:
            conn.close()