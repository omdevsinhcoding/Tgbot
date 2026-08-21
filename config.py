"""
Bot Configuration — loads settings from .env file.
"""

import os
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

# Admin Telegram IDs (list of integers)
ADMIN_IDS = [
    int(uid.strip())
    for uid in os.getenv("ADMIN_IDS", "").split(",")
    if uid.strip().isdigit()
]

# Support Contact
SUPPORT_USERNAME = os.getenv("SUPPORT_USERNAME", "@support")

# Button Labels (centralized so handlers reference the same strings)
BTN_PROFILE = "👤 Profile"
BTN_GET_EMAIL = "📧 Get Email"
BTN_DIRECT_LINK = "🔗 Direct Link"
BTN_TV_ACTIVATION = "📺 TV Activate"
BTN_SUPPORT = "🆘 Support"
BTN_ADMIN_PANEL = "⚙️ Admin Panel"

# Admin Sub-Menu Buttons
BTN_EDIT_WELCOME = "✏️ Edit Welcome Message"
BTN_MANAGE_PLANS = "📋 Manage Plans"
BTN_MANAGE_USER_PLANS = "👥 Manage User Plans"
BTN_BACK = "🔙 Back to Main Menu"

# Admin Plan Manager Sub-Buttons
BTN_CREATE_PLAN = "➕ Create Plan"
BTN_LIST_PLANS = "📄 List Plans"
BTN_DELETE_PLAN = "🗑️ Delete Plan"
BTN_BACK_ADMIN = "🔙 Back to Admin"
