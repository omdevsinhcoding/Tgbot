"""
Start Handler — /start command.
Shows rich welcome message matching the old bot style.
"""

from html import escape as html_escape

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from config import BRAND, SUPPORT_WA, SUPPORT_WA_LINK, BTN_CHECK_HOUSE, BTN_CHECK_TEMP, TICKET_RAISE, BTN_PROFILE
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

    # ── Check admin status for keyboard ─────────────────────
    admin = await is_user_admin(user.id)

    # ── Fetch welcome message from DB ───────────────────────
    welcome_msg = await get_setting("welcome_message", "")

    # ── Fetch active plans ──────────────────────────────────
    plans = await get_active_plans()

    if plans:
        plans_text = "\n📦 <b>Available Plans:</b>\n"
        for plan in plans:
            plans_text += (
                f"\n🔹 <b>{html_escape(plan['name'])}</b>\n"
                f"   ├ {html_escape(str(plan['description']))}\n"
                f"   ├ Duration: {plan['duration_days']} days\n"
                f"   ├ Max Emails: {plan['max_emails']}\n"
                f"   └ Price: ₹{plan['price']}\n"
            )
    else:
        plans_text = ""

    # ── Build rich welcome message (matches old bot) ────────
    full_message = (
        f"✨ <b>Welcome to {html_escape(BRAND)}</b>\n\n"
        f"Hi @{html_escape(user.username or 'user')} 👋\n"
        "Aap official verification system se connected ho.\n\n"

        "━━━━━━━━━━━━━━━━━━\n"
        "📌 <b>How It Works</b>\n"
        "• Bot k function ko use krne k liye niche k button use kijiyega\n"
        "• Required email receive hone do\n"
        "• Niche se correct option select karo\n"
        "• System unread mail scan karke valid link dega ⚡\n"
        "━━━━━━━━━━━━━━━━━━\n\n"

        "🔎 <b>Available Options</b>\n"
        f"{html_escape(BTN_CHECK_HOUSE)}\n"
        f"{html_escape(BTN_CHECK_TEMP)}\n"
        f"{html_escape(TICKET_RAISE)}\n"
        f"{html_escape(BTN_PROFILE)}\n\n"

        "━━━━━━━━━━━━━━━━━━\n"
        "⚠️ <b>Important</b>\n"
        "• Agar first attempt me link na mile, 30 sec wait karke dobara try karein 🔁\n"
        "• Kabhi-kabhi 2–3 attempts lag sakte hain\n"
        "• 3–4 tries ke baad bhi link na mile to support contact karein\n\n"

        f"📞 <b>Support:</b> {html_escape(SUPPORT_WA)}\n"
        f"{html_escape(SUPPORT_WA_LINK)}\n\n"

        "📌 Ensure karein ki Netflix ka code ya\n"
        "Household update email aapke device par receive ho chuka ho.\n\n"

        "Select an option to continue 👇"
    )

    if plans_text:
        full_message += "\n\n" + plans_text

    # ── Send message with keyboard ──────────────────────────
    await update.message.reply_text(
        full_message,
        parse_mode=ParseMode.HTML,
        reply_markup=get_main_menu(is_admin=admin),
        disable_web_page_preview=True,
    )
