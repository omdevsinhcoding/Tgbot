"""
Main Menu Keyboard — static ReplyKeyboardMarkup for all users.
Admin users get an extra "Admin Panel" button.
"""

from telegram import ReplyKeyboardMarkup, KeyboardButton
from config import (
    BTN_PROFILE, BTN_GET_EMAIL, BTN_DIRECT_LINK,
    BTN_TV_ACTIVATION, BTN_SUPPORT, BTN_ADMIN_PANEL,
)


def get_main_menu(is_admin: bool = False) -> ReplyKeyboardMarkup:
    """
    Build the main menu keyboard.
    Admins see an extra ⚙️ Admin Panel button at the bottom.
    """
    keyboard = [
        [KeyboardButton(BTN_PROFILE), KeyboardButton(BTN_GET_EMAIL)],
        [KeyboardButton(BTN_DIRECT_LINK), KeyboardButton(BTN_TV_ACTIVATION)],
        [KeyboardButton(BTN_SUPPORT)],
    ]

    if is_admin:
        keyboard.append([KeyboardButton(BTN_ADMIN_PANEL)])

    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        one_time_keyboard=False,
    )
