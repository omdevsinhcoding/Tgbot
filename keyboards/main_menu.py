"""
Main Menu Keyboard — matches the old bot layout exactly.
"""

from telegram import ReplyKeyboardMarkup, KeyboardButton
from config import (
    BTN_CHECK_HOUSE, BTN_CHECK_TEMP,
    BTN_PROFILE, BTN_HELP, BTN_ADMIN_PANEL,
)


def get_main_menu(is_admin: bool = False) -> ReplyKeyboardMarkup:
    """User main menu — same layout as old bot."""
    keyboard = [
        [KeyboardButton(BTN_CHECK_HOUSE), KeyboardButton(BTN_CHECK_TEMP)],
        [KeyboardButton(BTN_PROFILE), KeyboardButton(BTN_HELP)],
    ]
    if is_admin:
        keyboard.append([KeyboardButton(BTN_ADMIN_PANEL)])

    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
