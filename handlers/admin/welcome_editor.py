"""
Welcome Editor — admin can view and update the bot's welcome message.
Uses ConversationHandler for multi-step flow.
"""

from telegram import Update
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from utils.decorators import admin_only
from utils.helpers import get_setting, set_setting
from keyboards.admin_menu import get_admin_menu

# Conversation states
WAITING_FOR_WELCOME_MSG = 0


@admin_only
async def edit_welcome_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle the ✏️ Edit Welcome Message button.
    Shows current message and asks for the new one.
    """
    current_msg = await get_setting("welcome_message", "No welcome message set.")

    await update.message.reply_text(
        "✏️ *Edit Welcome Message*\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        "📝 *Current welcome message:*\n\n"
        f"{current_msg}\n\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "Send the *new welcome message* below.\n"
        "You can use Markdown formatting.\n\n"
        "Send /cancel to cancel.",
        parse_mode="Markdown",
    )
    return WAITING_FOR_WELCOME_MSG


async def save_welcome_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Save the new welcome message to the database."""
    new_message = update.message.text

    await set_setting("welcome_message", new_message)

    await update.message.reply_text(
        "✅ *Welcome message updated successfully!*\n\n"
        "New users will now see the updated message.",
        parse_mode="Markdown",
        reply_markup=get_admin_menu(),
    )
    return ConversationHandler.END


async def cancel_welcome_edit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel the welcome message edit."""
    await update.message.reply_text(
        "❌ Edit cancelled.",
        reply_markup=get_admin_menu(),
    )
    return ConversationHandler.END


def get_welcome_editor_conversation() -> ConversationHandler:
    """Build the ConversationHandler for welcome message editing."""
    from telegram.ext import CommandHandler

    return ConversationHandler(
        entry_points=[
            MessageHandler(
                filters.Regex(r"^✏️ Edit Welcome Message$"),
                edit_welcome_handler,
            ),
        ],
        states={
            WAITING_FOR_WELCOME_MSG: [
                CommandHandler("cancel", cancel_welcome_edit),
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    save_welcome_message,
                ),
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel_welcome_edit),
        ],
    )
