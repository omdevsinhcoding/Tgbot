"""
Helpers — common utility functions used across the bot.
"""

from database.connection import get_pool


async def get_setting(key: str, default: str = "") -> str:
    """Fetch a setting value from the settings table."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        value = await conn.fetchval(
            "SELECT value FROM settings WHERE key = $1", key
        )
    return value if value is not None else default


async def set_setting(key: str, value: str):
    """Insert or update a setting in the settings table."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO settings (key, value, updated_at)
            VALUES ($1, $2, NOW())
            ON CONFLICT (key)
            DO UPDATE SET value = $2, updated_at = NOW()
            """,
            key, value,
        )


async def is_user_admin(telegram_id: int) -> bool:
    """Check if a user is an admin in the database."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        result = await conn.fetchval(
            "SELECT is_admin FROM users WHERE telegram_id = $1",
            telegram_id,
        )
    return bool(result)


async def get_active_plans() -> list:
    """Fetch all active plans from the database."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT * FROM plans WHERE is_active = TRUE ORDER BY price ASC"
        )
    return [dict(row) for row in rows]
