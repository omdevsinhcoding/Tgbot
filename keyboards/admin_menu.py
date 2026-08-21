"""
Admin Menu Keyboard — sub-menu for admin panel operations.
"""

from telegram import ReplyKeyboardMarkup, KeyboardButton
from config import (
    BTN_EDIT_WELCOME, BTN_MANAGE_PLANS,
    BTN_MANAGE_USER_PLANS, BTN_BACK,
    BTN_CREATE_PLAN, BTN_LIST_PLANS,
    BTN_DELETE_PLAN, BTN_BACK_ADMIN,
)


def get_admin_menu() -> ReplyKeyboardMarkup:
    """Admin panel sub-menu keyboard."""
    keyboard = [
        [KeyboardButton(BTN_EDIT_WELCOME)],
        [KeyboardButton(BTN_MANAGE_PLANS)],
        [KeyboardButton(BTN_MANAGE_USER_PLANS)],
        [KeyboardButton(BTN_BACK)],
    ]
    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        one_time_keyboard=False,
    )


def get_plan_manager_menu() -> ReplyKeyboardMarkup:
    """Plan management sub-menu keyboard."""
    keyboard = [
        [KeyboardButton(BTN_CREATE_PLAN)],
        [KeyboardButton(BTN_LIST_PLANS)],
        [KeyboardButton(BTN_DELETE_PLAN)],
        [KeyboardButton(BTN_BACK_ADMIN)],
    ]
    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        one_time_keyboard=False,
    )
