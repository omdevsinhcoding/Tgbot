"""
Get Email Handler — scans user's assigned IMAP accounts for Netflix emails.
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
    """Handle Check Update Household button."""
    await _scan_and_reply(update, context, "household")


async def check_temp_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle Check Temporary Code button."""
    await _scan_and_reply(update, context, "temp")


get_email_handler = check_household_handler


async def _scan_and_reply(update: Update, context: ContextTypes.DEFAULT_TYPE, mode: str):
    """Core scan function."""
    user = update.effective_user
    user_id = user.id

    # ── Rate limiting ───────────────────────────────
    now = time.time()
    last_scan = user_cooldown.get(user_id, 0)
    if now - last_scan < SCAN_COOLDOWN:
        remaining = int(SCAN_COOLDOWN - (now - last_scan))
        await update.message.reply_text(
            f"<b>Please wait {remaining} seconds</b> before your next scan.",
            parse_mode=ParseMode.HTML,
        )
        return
    user_cooldown[user_id] = now

    # ── Get user's assigned IMAP accounts ───────────
    accounts = await get_user_imap_accounts(user_id)
    if not accounts:
        admin = await is_user_admin(user_id)
        await update.message.reply_text(
            f"<b>No Email Account Assigned</b>\n\n"
            f"@{html_escape(user.username or 'user')}, you don't have any email account assigned yet.\n\n"
            f"Please contact admin to get an account assigned.\n\n"
            f"Support: <b>{html_escape(SUPPORT_WA)}</b>\n"
            f"{html_escape(SUPPORT_WA_LINK)}",
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
            reply_markup=get_main_menu(is_admin=admin),
        )
        return

    label = "Household" if mode == "household" else "Temporary Code"

    # ── Show scanning message ───────────────────────
    scan_msg = await update.message.reply_text(
        f"<b>Establishing secure connection...</b>\n\n"
        f"Inbox access granted.\n\n"
        f"Scanning for new emails...\n"
        f"Please wait while we find your verification link.\n\n"
        f"If not found on first try, tap the button again.\n"
        f"After 3-4 attempts, please contact support.\n\n"
        f"@{html_escape(user.username or 'user')}\n"
        f"Scan in progress...",
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
        try:
            await scan_msg.delete()
        except Exception:
            pass
        await update.message.reply_text(
            f"<b>No Matching Email Found</b>\n\n"
            f"@{html_escape(user.username or 'user')}, the required email was not found.\n\n"
            f"Possible reasons:\n"
            f"  - Email has already been read\n"
            f"  - Email hasn't arrived yet\n\n"
            f"Please request a new email and try again.\n\n"
            f"Status: <i>{html_escape(status)}</i>",
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
            reply_markup=get_main_menu(is_admin=admin),
        )
        return

    # ── FOUND! ─────────────────────────────────────
    try:
        await scan_msg.delete()
    except Exception:
        pass
    safe_link = hit.link

    if mode == "household":
        found_text = (
            f"<b>Household Verification Link Found!</b>\n\n"
            f"@{html_escape(user.username or 'user')}, your link is ready.\n\n"
            f"Subject: <i>{html_escape(hit.subject[:60])}</i>\n"
            f"From: <i>{html_escape(hit.sender[:40])}</i>\n"
            f"Date: <i>{html_escape(hit.date[:30])}</i>\n\n"
            f"Click the button below to update your household.\n"
            f"Complete the process on the Netflix page."
        )
    else:
        found_text = (
            f"<b>Temporary Code Link Found!</b>\n\n"
            f"@{html_escape(user.username or 'user')}, your link is ready.\n\n"
            f"Subject: <i>{html_escape(hit.subject[:60])}</i>\n"
            f"From: <i>{html_escape(hit.sender[:40])}</i>\n"
            f"Date: <i>{html_escape(hit.date[:30])}</i>\n\n"
            f"Click the button below to get your temporary code.\n"
            f"Enter the code on your Netflix device."
        )

    await update.message.reply_text(
        found_text,
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Open Link", url=safe_link)]
        ]),
    )

    await update.message.reply_text(
        f"<b>Thank you for using {html_escape(BRAND)}!</b>\n\n"
        f"If you need help, contact support.",
        parse_mode=ParseMode.HTML,
        reply_markup=get_main_menu(is_admin=admin),
    )
