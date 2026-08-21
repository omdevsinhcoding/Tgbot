"""
Database Connection — manages asyncpg connection pool.
"""

import asyncpg
from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD

# Global connection pool
pool: asyncpg.Pool | None = None


async def create_pool():
    """Create and return the asyncpg connection pool."""
    global pool
    pool = await asyncpg.create_pool(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        min_size=2,
        max_size=10,
    )
    return pool


async def get_pool() -> asyncpg.Pool:
    """Get the existing pool or create one."""
    global pool
    if pool is None:
        await create_pool()
    return pool


async def close_pool():
    """Close the connection pool gracefully."""
    global pool
    if pool:
        await pool.close()
        pool = None
