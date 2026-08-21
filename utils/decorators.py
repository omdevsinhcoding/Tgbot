"""
Decorators — reusable access-control decorators for handlers.
"""

from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes

from database.connection import get_pool


def admin_only(func):
    """
    Decorator that restricts a handler to admin users only.
    Checks the `is_admin` flag in the database.
    """
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id
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
