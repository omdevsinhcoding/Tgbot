"""
Helpers — common utility functions used across the bot.
"""

from typing import List, Dict, Optional
from database.connection import get_pool
from config import ADMIN_IDS, OWNER_IDS


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
    """Check if a user is an admin (DB flag OR env ADMIN_IDS/OWNER_IDS)."""
    if telegram_id in OWNER_IDS or telegram_id in ADMIN_IDS:
        return True
    pool = await get_pool()
    async with pool.acquire() as conn:
        result = await conn.fetchval(
            "SELECT is_admin FROM users WHERE telegram_id = $1",
            telegram_id,
        )
    return bool(result)


def is_owner(telegram_id: int) -> bool:
    """Check if user is an owner."""
    return telegram_id in OWNER_IDS


async def get_active_plans() -> list:
    """Fetch all active plans from the database."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT * FROM plans WHERE is_active = TRUE ORDER BY price ASC"
        )
    return [dict(row) for row in rows]


async def get_user_imap_accounts(telegram_id: int) -> List[Dict]:
    """Get all IMAP accounts assigned to a user."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT ia.id, ia.email, ia.password, ia.host, ia.port, ia.label
            FROM imap_accounts ia
            JOIN user_imap_assignments uia ON ia.id = uia.imap_account_id
            WHERE uia.telegram_id = $1 AND ia.is_active = TRUE
            ORDER BY ia.id
            """,
            telegram_id,
        )
    return [dict(row) for row in rows]


async def get_rules(rule_type: str) -> List[str]:
    """Get all rules of a given type from the rules table."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT rule_value FROM rules WHERE rule_type = $1 ORDER BY id ASC",
            rule_type,
        )
    return [row["rule_value"] for row in rows]
