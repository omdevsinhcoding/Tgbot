"""
Profile Handler — shows user profile info from the database.
"""

from telegram import Update
from telegram.ext import ContextTypes

from database.connection import get_pool


async def profile_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the 👤 Profile button press."""
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

    # ── Format plan info ────────────────────────────────────
    if row["plan_name"]:
        plan_info = f"📦 *Plan:* {row['plan_name']}"
        if row["plan_expires_at"]:
            expiry = row["plan_expires_at"].strftime("%d %b %Y, %I:%M %p")
            plan_info += f"\n⏳ *Expires:* {expiry}"
        else:
            plan_info += "\n⏳ *Expires:* Never"
    else:
        plan_info = "📦 *Plan:* No active plan"

    # ── Format profile message ──────────────────────────────
    joined = row["created_at"].strftime("%d %b %Y")

    profile_text = (
        f"👤 *Your Profile*\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"
        f"🆔 *Telegram ID:* `{row['telegram_id']}`\n"
        f"📛 *Name:* {row['full_name'] or 'N/A'}\n"
        f"👤 *Username:* @{row['username'] or 'N/A'}\n\n"
        f"{plan_info}\n\n"
        f"📅 *Joined:* {joined}\n"
        f"🛡️ *Role:* {'Admin' if row['is_admin'] else 'User'}"
    )

    await update.message.reply_text(profile_text, parse_mode="Markdown")
