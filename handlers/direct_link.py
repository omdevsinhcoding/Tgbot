"""
Direct Link Handler — placeholder for direct link generation.
Will be implemented in Phase 2.
"""

from telegram import Update
from telegram.ext import ContextTypes


async def direct_link_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the 🔗 Direct Link button press."""
    await update.message.reply_text(
        "🔗 *Direct Link Generator*\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        "🚧 This feature is coming soon!\n\n"
        "Generate direct download links for your emails "
        "and attachments.",
        parse_mode="Markdown",
    )
