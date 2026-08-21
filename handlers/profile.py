"""
Profile Handler — shows user profile with old bot styling.
"""

from html import escape as html_escape

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from config import BRAND
from database.connection import get_pool


async def profile_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the 👤 User Profile button press."""
    user = update.effective_user
    pool = await get_pool()

    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT u.*, p.name AS plan_name
            FROM users u
            LEFT JOIN plans p ON u.plan_id = p.id
            WHERE u.telegram_id = $1
            """,
            user.id,
        )

    if not row:
        await update.message.reply_text("❌ Profile not found. Please /start first.")
        return

    # Plan info
    if row["plan_name"]:
        plan_info = f"📦 Plan: <b>{html_escape(row['plan_name'])}</b>"
        if row["plan_expires_at"]:
            expiry = row["plan_expires_at"].strftime("%d %b %Y, %I:%M %p")
            plan_info += f"\n⏳ Expires: {expiry}"
    else:
        plan_info = "📦 Plan: <b>No active plan</b>"

    joined = row["created_at"].strftime("%d %b %Y") if row["created_at"] else "-"

    await update.message.reply_text(
        f"👤 <b>Your Profile — {html_escape(BRAND)}</b>\n\n"
        f"🆔 ID: <code>{row['telegram_id']}</code>\n"
        f"👤 Username: <b>@{html_escape(user.username or '-')}</b>\n"
        f"📝 Name: <b>{html_escape(row['full_name'] or '-')}</b>\n\n"
        f"{plan_info}\n\n"
        f"📅 Joined: {joined}\n"
        f"✅ Status: Active",
        parse_mode=ParseMode.HTML,
    )
