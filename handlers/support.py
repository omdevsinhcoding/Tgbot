"""
Support Handler — shows support contact info.
"""

from telegram import Update
from telegram.ext import ContextTypes

from config import SUPPORT_USERNAME


async def support_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the 🆘 Support button press."""
    await update.message.reply_text(
        "🆘 *Support*\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        "Need help? Contact our support team:\n\n"
        f"📩 *Telegram:* {SUPPORT_USERNAME}\n\n"
        "We typically respond within 24 hours.",
        parse_mode="Markdown",
    )
