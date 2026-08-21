"""
Support Handler — shows help and support information.
"""

from html import escape as html_escape

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from config import BRAND, SUPPORT_WA, SUPPORT_WA_LINK, BTN_CHECK_HOUSE, BTN_CHECK_TEMP


async def support_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the ❓ Help & Support button press."""
    await update.message.reply_text(
        f"❓ <b>Help & Support — {html_escape(BRAND)}</b>\n\n"
        "✅ Use:\n"
        f"• {html_escape(BTN_CHECK_HOUSE)} — household verification link\n"
        f"• {html_escape(BTN_CHECK_TEMP)} — temporary code/verify link\n\n"
        f"📞 WhatsApp Support: <b>{html_escape(SUPPORT_WA)}</b>\n"
        f"{html_escape(SUPPORT_WA_LINK)}\n\n"
        "Koi issue ho to ticket raise karo ya WhatsApp pe message karo 👇",
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
    )
