"""
Admin Panel Handler — entry point for admin panel with inline buttons.
Handles all admin callback queries and routes to the right function.
"""

from telegram import Update
from telegram.ext import ContextTypes

from utils.decorators import admin_only
from keyboards.admin_menu import get_admin_menu
from keyboards.main_menu import get_main_menu


@admin_only
async def admin_panel_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the ⚙️ Admin Panel button press (ReplyKeyboard)."""
    await update.message.reply_text(
        "⚙️ *Admin Panel*\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        "Welcome, Admin! Choose an option:",
        parse_mode="Markdown",
        reply_markup=get_admin_menu(),
    )


async def admin_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Central callback router for all admin inline buttons.
    Routes based on callback_data prefix 'admin:'.
    """
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    # Check admin in DB
    from utils.helpers import is_user_admin
    if not await is_user_admin(user_id):
        await query.answer("⛔ Access denied.", show_alert=True)
        return

    data = query.data  # e.g. "admin:welcome", "admin:plans"

    if data == "admin:panel":
        # Show admin panel
        await query.message.edit_text(
            "⚙️ *Admin Panel*\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            "Welcome, Admin! Choose an option:",
            parse_mode="Markdown",
            reply_markup=get_admin_menu(),
        )

    elif data == "admin:back":
        # Back to main menu — delete inline message, send new with reply keyboard
        await query.message.delete()
        is_admin = await is_user_admin(user_id)
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text="🏠 *Main Menu*\n\nChoose an option:",
            parse_mode="Markdown",
            reply_markup=get_main_menu(is_admin=is_admin),
        )

    elif data == "admin:welcome":
        # Start welcome edit flow
        from handlers.admin.welcome_editor import start_welcome_edit_callback
        await start_welcome_edit_callback(update, context)

    elif data == "admin:plans":
        # Show plan manager sub-menu
        from keyboards.admin_menu import get_plan_manager_menu
        await query.message.edit_text(
            "📋 *Plan Manager*\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            "Choose an action:",
            parse_mode="Markdown",
            reply_markup=get_plan_manager_menu(),
        )

    elif data == "admin:create_plan":
        from handlers.admin.plan_manager import start_create_plan_callback
        await start_create_plan_callback(update, context)

    elif data == "admin:list_plans":
        from handlers.admin.plan_manager import list_plans_callback
        await list_plans_callback(update, context)

    elif data == "admin:delete_plan":
        from handlers.admin.plan_manager import start_delete_plan_callback
        await start_delete_plan_callback(update, context)

    elif data == "admin:user_plans":
        from handlers.admin.user_plan import start_user_plan_callback
        await start_user_plan_callback(update, context)
