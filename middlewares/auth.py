"""
Auth Middleware — auto-registers users on first interaction.
Also syncs admin status from config on every interaction.
"""

from database.connection import get_pool
from config import ADMIN_IDS


async def ensure_user_registered(telegram_id: int, username: str, full_name: str):
    """
    Register user in the database if they don't exist yet.
    If the user's telegram_id is in ADMIN_IDS (from .env),
    automatically mark them as admin.
    """
    pool = await get_pool()

    is_admin = telegram_id in ADMIN_IDS

    async with pool.acquire() as conn:
        # Try to insert new user; on conflict just update username/full_name
        await conn.execute(
            """
            INSERT INTO users (telegram_id, username, full_name, is_admin)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (telegram_id)
            DO UPDATE SET
                username  = $2,
                full_name = $3,
                is_admin  = CASE
                    WHEN $4 = TRUE THEN TRUE
                    ELSE users.is_admin
                END
            """,
            telegram_id,
            username or "",
            full_name or "",
            is_admin,
        )
