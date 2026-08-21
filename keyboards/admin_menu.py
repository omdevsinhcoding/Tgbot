"""
Admin Menu Keyboard — Inline buttons for admin panel.
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def get_admin_menu() -> InlineKeyboardMarkup:
    """Admin panel inline keyboard."""
    keyboard = [
        [InlineKeyboardButton("✏️ Edit Welcome Message", callback_data="admin:welcome")],
        [InlineKeyboardButton("📋 Manage Plans", callback_data="admin:plans")],
        [InlineKeyboardButton("👥 Manage User Plans", callback_data="admin:user_plans")],
        [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="admin:back")],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_plan_manager_menu() -> InlineKeyboardMarkup:
    """Plan management inline keyboard."""
    keyboard = [
        [InlineKeyboardButton("➕ Create Plan", callback_data="admin:create_plan")],
        [InlineKeyboardButton("📄 List Plans", callback_data="admin:list_plans")],
        [InlineKeyboardButton("🗑️ Delete Plan", callback_data="admin:delete_plan")],
        [InlineKeyboardButton("🔙 Back to Admin", callback_data="admin:panel")],
    ]
    return InlineKeyboardMarkup(keyboard)
