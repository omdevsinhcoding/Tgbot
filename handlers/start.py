"""
Start Handler — /start command.
Shows welcome message + active plans + main menu keyboard.
"""

from telegram import Update
from telegram.ext import ContextTypes

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

    # ── Fetch welcome message from DB ───────────────────────
    welcome_msg = await get_setting(
        "welcome_message",
        "👋 Welcome to the Bot!"
    )

    # ── Fetch active plans ──────────────────────────────────
    plans = await get_active_plans()

    if plans:
        plans_text = "\n\n📦 *Available Plans:*\n"
        for plan in plans:
            plans_text += (
                f"\n🔹 *{plan['name']}*\n"
                f"   ├ {plan['description']}\n"
                f"   ├ Duration: {plan['duration_days']} days\n"
                f"   ├ Max Emails: {plan['max_emails']}\n"
                f"   └ Price: ₹{plan['price']}\n"
            )
    else:
        plans_text = "\n\n📦 _No plans available yet._"

    full_message = welcome_msg + plans_text

    # ── Check admin status for keyboard ─────────────────────
    admin = await is_user_admin(user.id)

    # ── Send message with keyboard ──────────────────────────
    await update.message.reply_text(
        full_message,
        parse_mode="Markdown",
        reply_markup=get_main_menu(is_admin=admin),
    )
