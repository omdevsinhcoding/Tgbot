"""
Support Handler — shows help and support information.
"""

from html import escape as html_escape

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from config import BRAND, SUPPORT_WA, SUPPORT_WA_LINK


async def support_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the Help & Support button press."""
    await update.message.reply_text(
        f"<b>Help &amp; Support - {html_escape(BRAND)}</b>\n\n"
        f"<b>Available Features:</b>\n"
        f"  Check Update Household - Get household verification link\n"
        f"  Check Temporary Code - Get temporary access code link\n\n"
        f"<b>Contact Support:</b>\n"
        f"WhatsApp: <b>{html_escape(SUPPORT_WA)}</b>\n"
        f"{html_escape(SUPPORT_WA_LINK)}\n\n"
        f"If you're facing any issues, please contact support.",
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
    )
