"""
Bot Configuration — loads settings from .env file.
"""

import os
import re
from dotenv import load_dotenv

load_dotenv()

# Telegram Bot Token
BOT_TOKEN = os.getenv("BOT_TOKEN", "")

# PostgreSQL Database Config
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_NAME = os.getenv("DB_NAME", "tgbot")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")

# Admin + Owner IDs
OWNER_IDS = set(
    int(x) for x in os.getenv("OWNER_IDS", "").replace(" ", "").split(",") if x.isdigit()
)
ADMIN_IDS = set(
    int(x) for x in os.getenv("ADMIN_IDS", "").replace(" ", "").split(",") if x.isdigit()
)

# Support WhatsApp
SUPPORT_WA = os.getenv("SUPPORT_WA", "+919888646106").strip()
SUPPORT_WA_LINK = f"https://wa.me/{re.sub(r'[^0-9]', '', SUPPORT_WA)}"

# Brand
BRAND = "Premium Stuff™"

# Rate Limiting
SCAN_COOLDOWN = 30  # seconds

# Auto-Delete (48 hours)
AUTO_DELETE_DELAY = 172800

# ═══════════════════════════════════════════════
# Button Labels (User Main Menu — ReplyKeyboard)
# ═══════════════════════════════════════════════
BTN_CHECK_HOUSE = "✅ Check Update Household"
BTN_CHECK_TEMP = "🔐 Check Temporary Code"
BTN_PROFILE = "👤 User Profile"
BTN_HELP = "❓ Help & Support"
BTN_ADMIN_PANEL = "🛡 Admin Panel"
BTN_CANCEL = "Cancel"
BTN_BACK = "🔙 Back"

# Ticket
TICKET_RAISE = "🧾 Raise a Ticket"

# Legacy names kept for bot.py imports (mapped)
BTN_GET_EMAIL = BTN_CHECK_HOUSE
BTN_DIRECT_LINK = BTN_CHECK_TEMP
BTN_TV_ACTIVATION = TICKET_RAISE
BTN_SUPPORT = BTN_HELP
