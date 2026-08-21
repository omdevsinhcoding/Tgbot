"""
TV Activation Handler — placeholder for TV activation feature.
Will be implemented in Phase 2.
"""

from telegram import Update
from telegram.ext import ContextTypes


async def tv_activation_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the 📺 TV Activate button press."""
    await update.message.reply_text(
        "📺 *TV Activation*\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        "🚧 This feature is coming soon!\n\n"
        "Activate streaming services on your TV "
        "using email verification codes.",
        parse_mode="Markdown",
    )
