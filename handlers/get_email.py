"""
Get Email Handler — scans user's assigned IMAP accounts for Netflix emails.
Ported from old monolithic bot with full styling.
"""

import asyncio
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from html import escape as html_escape

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from config import BRAND, SUPPORT_WA, SUPPORT_WA_LINK, SCAN_COOLDOWN
from utils.helpers import get_user_imap_accounts, get_rules, is_user_admin
from keyboards.main_menu import get_main_menu
from services.imap_scanner import imap_scan_last10_unseen, mask_token_in_url

# Rate limiting per user
user_cooldown: dict = defaultdict(float)

# Thread pool for blocking IMAP operations
scan_executor = ThreadPoolExecutor(max_workers=4)


async def check_household_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle ✅ Check Update Household button."""
    await _scan_and_reply(update, context, "household")


async def check_temp_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle 🔐 Check Temporary Code button."""
    await _scan_and_reply(update, context, "temp")


# Keep old name for backward compat
get_email_handler = check_household_handler


async def _scan_and_reply(update: Update, context: ContextTypes.DEFAULT_TYPE, mode: str):
    """Core scan function — checks rate limit, scans IMAP, replies with result."""
    user = update.effective_user
    user_id = user.id

    # ── Rate limiting ───────────────────────────────
    now = time.time()
    last_scan = user_cooldown.get(user_id, 0)
    if now - last_scan < SCAN_COOLDOWN:
        remaining = int(SCAN_COOLDOWN - (now - last_scan))
        await update.message.reply_text(
            f"⏳ Please wait <b>{remaining}</b> seconds before next scan.",
            parse_mode=ParseMode.HTML,
        )
        return
    user_cooldown[user_id] = now

    # ── Get user's assigned IMAP accounts ───────────
    accounts = await get_user_imap_accounts(user_id)
    if not accounts:
        admin = await is_user_admin(user_id)
        await update.message.reply_text(
            f"⚠️ <b>No IMAP account assigned</b>\n\n"
            f"@{html_escape(user.username or 'user')}, aapko abhi koi email account assign nahi hua hai.\n\n"
            f"Admin se contact karo ya support pe message karo.\n\n"
            f"📞 WhatsApp: <b>{html_escape(SUPPORT_WA)}</b>\n"
            f"{html_escape(SUPPORT_WA_LINK)}",
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
            reply_markup=get_main_menu(is_admin=admin),
        )
        return

    label = "Household" if mode == "household" else "Temporary Code"

    # ── Show scanning message ───────────────────────
    scan_msg = await update.message.reply_text(
        f"🔌 <b>Secure connection establish ho chuka hai...</b>\n\n"
        f"📬 Inbox access granted.\n\n"
        f"New mails check kiye ja rahe hai...\n"
        f"Wait kijiye link milega link pr tap krke aage continue kijiye...\n\n"
        f"agar na mile to firse button ko tap kijiye mil jayega\n"
        f"agar 3-4 bar me na mile to hame whatsapp pr msg kijiyega.\n"
        f"@{html_escape(user.username or 'user')}...\n"
        f"Mission in progress. 🎯",
        parse_mode=ParseMode.HTML,
    )

    # ── Get mail rules from DB ──────────────────────
    sender_rules = await get_rules("sender_allow")
    if not sender_rules:
        sender_rules = ["info@account.netflix.com", "@netflix.com"]

    subject_key = "household_subject" if mode == "household" else "temp_subject"
    subject_rules = await get_rules(subject_key)
    if not subject_rules:
        if mode == "household":
            subject_rules = ["update your netflix household", "how to update your netflix household"]
        else:
            subject_rules = ["temporary access code", "your netflix temporary access code"]

    # ── Scan ALL assigned IMAP accounts ─────────────
    loop = asyncio.get_event_loop()
    hit = None
    status = "No matching email found."

    for account in accounts:
        result_hit, result_status = await loop.run_in_executor(
            scan_executor,
            imap_scan_last10_unseen,
            account["email"],
            account["password"],
            account["host"],
            account["port"],
            mode,
            sender_rules,
            subject_rules,
        )
        if result_hit:
            hit = result_hit
            status = result_status
            break
        status = result_status

    admin = await is_user_admin(user_id)

    if hit is None:
        # ── NOT FOUND ──────────────────────────────
        await scan_msg.delete()
        await update.message.reply_text(
            f"📭 <b>Aaj inbox thoda khamosh hai...</b>\n\n"
            f"@{html_escape(user.username or 'user')}, required mail abhi tak locate nahi hua.\n\n"
            "Possible reasons:\n"
            "• Mail unread nahi hai\n"
            "• Abhi receive nahi hua\n\n"
            "🔁 Fresh request bhejiye aur phir try kijiye.\n\n"
            f"Kahaani abhi khatam nahi hui. 💎",
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
            reply_markup=get_main_menu(is_admin=admin),
        )
        return

    # ── FOUND! ─────────────────────────────────────
    await scan_msg.delete()
    safe_link = hit.link

    if mode == "household":
        found_text = (
            f"Netflix: 😎 <i>Link ko pakadna mushkil hi nahi... namumkin hai.</i>\n\n"
            f"Lekin...\n\n"
            f"{html_escape(BRAND)}: 🏠 Household verification link ko dhoondhna?\n\n"
            f"Woh kaam {html_escape(BRAND)} ka hai. 💎\n\n"
            f"@{html_escape(user.username or 'user')}...\n"
            f"Jo chahiye tha... woh mil gaya.\n\n"
            f"🔗 <b>Household Update Link ready hai.</b>\n\n"
            f"Der mat karo...\n"
            f"Click karo aur update complete karo. ⚡\n\n"
            f"Baaki system sambhal lega."
        )
    else:
        found_text = (
            f"Netflix: 😎 <i>Code milna aasaan nahi hota...</i>\n\n"
            f"Lekin...\n\n"
            f"{html_escape(BRAND)}: 🔐 Temporary verification link ko locate karna?\n\n"
            f"Woh hamara kaam hai. 💎\n\n"
            f"@{html_escape(user.username or 'user')}...\n"
            f"Target secure ho chuka hai.\n\n"
            f"🔗 <b>Temporary Code Link ready hai.</b>\n\n"
            f"Click karo... code generate karo... access confirm karo. ⚡\n\n"
            f"System apna kaam kar chuka hai."
        )

    await update.message.reply_text(
        found_text,
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔗 Open Link", url=safe_link)]
        ]),
    )

    # Thank you message
    await update.message.reply_text(
        f"🙏 <b>Thank you for using {html_escape(BRAND)}!</b>\n\n"
        f"Link use kar liya? Hope sab smooth raha. 💎",
        parse_mode=ParseMode.HTML,
        reply_markup=get_main_menu(is_admin=admin),
    )
