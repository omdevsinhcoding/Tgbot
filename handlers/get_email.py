"""
Get Email Handler — placeholder for IMAP email functionality.
Will be implemented in Phase 2.
"""

from telegram import Update
from telegram.ext import ContextTypes


async def get_email_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the 📧 Get Email button press."""
    await update.message.reply_text(
        "📧 *Get Email*\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        "🚧 This feature is coming soon!\n\n"
        "You'll be able to access your IMAP emails "
        "directly from Telegram.",
        parse_mode="Markdown",
    )
