"""
Start Handler — /start command.
Shows welcome message + plans + main menu.
"""

from html import escape as html_escape

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from config import BRAND, SUPPORT_WA, SUPPORT_WA_LINK
from middlewares.auth import ensure_user_registered
from keyboards.main_menu import get_main_menu
from utils.helpers import get_setting, get_active_plans, is_user_admin


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /start command."""
    user = update.effective_user

    # ── Auto-register user ──────────────────────────────────
    await ensure_user_registered(
        telegram_id=user.id,
        username=user.username,
        full_name=user.full_name,
    )

    # ── Check admin status ──────────────────────────────────
    admin = await is_user_admin(user.id)

    # ── Fetch active plans ──────────────────────────────────
    plans = await get_active_plans()

    if plans:
        plans_text = "\n\n<b>Available Plans:</b>\n"
        for plan in plans:
            plans_text += (
                f"\n<b>{html_escape(plan['name'])}</b>\n"
                f"   {html_escape(str(plan['description']))}\n"
                f"   Duration: {plan['duration_days']} days\n"
                f"   Max Emails: {plan['max_emails']}\n"
                f"   Price: {plan['price']}\n"
            )
    else:
        plans_text = ""

    # ── Build welcome message ───────────────────────────────
    full_message = (
        f"<b>Welcome to {html_escape(BRAND)}</b>\n\n"
        f"Hi @{html_escape(user.username or 'user')}\n"
        f"You are connected to the official verification system.\n\n"

        f"<b>How It Works</b>\n"
        f"1. Make sure the required email has been received\n"
        f"2. Select the correct option from the menu below\n"
        f"3. The system will scan unread emails and provide the valid link\n\n"

        f"<b>Available Options</b>\n"
        f"  Check Update Household - Get household verification link\n"
        f"  Check Temporary Code - Get temporary access code link\n"
        f"  User Profile - View your profile information\n"
        f"  Help &amp; Support - Get help or raise a ticket\n\n"

        f"<b>Important</b>\n"
        f"  - If the link is not found on the first try, wait 30 seconds and try again\n"
        f"  - Sometimes 2-3 attempts may be needed\n"
        f"  - After 3-4 tries, contact support\n\n"

        f"Support: <b>{html_escape(SUPPORT_WA)}</b>\n"
        f"{html_escape(SUPPORT_WA_LINK)}\n\n"

        f"Select an option below to continue."
    )

    if plans_text:
        full_message += plans_text

    # ── Send message with keyboard ──────────────────────────
    await update.message.reply_text(
        full_message,
        parse_mode=ParseMode.HTML,
        reply_markup=get_main_menu(is_admin=admin),
        disable_web_page_preview=True,
    )
