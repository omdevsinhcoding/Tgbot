"""
Admin Panel Handler — entry point for the admin sub-menu.
Only accessible to users with is_admin=TRUE in the database.
"""

from telegram import Update
from telegram.ext import ContextTypes

from utils.decorators import admin_only
from keyboards.admin_menu import get_admin_menu
from keyboards.main_menu import get_main_menu


@admin_only
async def admin_panel_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the ⚙️ Admin Panel button press."""
    await update.message.reply_text(
        "⚙️ *Admin Panel*\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        "Welcome, Admin! Choose an option:",
        parse_mode="Markdown",
        reply_markup=get_admin_menu(),
    )


@admin_only
async def back_to_main_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the 🔙 Back to Main Menu button press."""
    # Clear any conversation state
    context.user_data.clear()

    await update.message.reply_text(
        "🏠 *Main Menu*\n\nChoose an option:",
        parse_mode="Markdown",
        reply_markup=get_main_menu(is_admin=True),
    )
