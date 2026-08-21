"""
Decorators — reusable access-control decorators for handlers.
"""

from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes

from config import ADMIN_IDS, OWNER_IDS
from database.connection import get_pool


def admin_only(func):
    """
    Decorator that restricts a handler to admin users only.
    Checks env ADMIN_IDS/OWNER_IDS first, then DB is_admin flag.
    """
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id

        # Check env config first (instant)
        if user_id in OWNER_IDS or user_id in ADMIN_IDS:
            return await func(update, context, *args, **kwargs)

        # Fallback to DB check
        pool = await get_pool()
        async with pool.acquire() as conn:
            is_admin = await conn.fetchval(
                "SELECT is_admin FROM users WHERE telegram_id = $1",
                user_id,
            )

        if not is_admin:
            await update.message.reply_text("⛔ Access denied. Admins only.")
            return

        return await func(update, context, *args, **kwargs)

    return wrapper
