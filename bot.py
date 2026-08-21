"""
Bot Entry Point — initializes the bot, database, and registers all handlers.
"""

import asyncio
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

from config import (
    BOT_TOKEN,
    BTN_PROFILE, BTN_GET_EMAIL, BTN_DIRECT_LINK,
    BTN_TV_ACTIVATION, BTN_SUPPORT, BTN_ADMIN_PANEL,
)

# Database
from database.connection import create_pool, close_pool
from database.models import init_database

# Handlers
from handlers.start import start_handler
from handlers.profile import profile_handler
from handlers.get_email import get_email_handler
from handlers.direct_link import direct_link_handler
from handlers.tv_activation import tv_activation_handler
from handlers.support import support_handler

# Admin Handlers
from handlers.admin.panel import admin_panel_handler, admin_callback_handler
from handlers.admin.welcome_editor import get_welcome_editor_conversation
from handlers.admin.plan_manager import (
    get_create_plan_conversation,
    get_delete_plan_conversation,
)
from handlers.admin.user_plan import get_user_plan_conversation


async def post_init(application):
    """Called after the Application is initialized — set up DB."""
    await create_pool()
    await init_database()
    print("🤖 Bot is starting...")


async def post_shutdown(application):
    """Called on shutdown — clean up DB pool."""
    await close_pool()
    print("🤖 Bot stopped. Database pool closed.")


def main():
    """Build and run the bot."""
    if not BOT_TOKEN:
        print("❌ BOT_TOKEN not set! Copy .env.example to .env and fill in your token.")
        return

    # ── Build Application ───────────────────────────────────
    app = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .post_init(post_init)
        .post_shutdown(post_shutdown)
        .build()
    )

    # ── Register ConversationHandlers FIRST (higher priority) ──
    app.add_handler(get_welcome_editor_conversation())
    app.add_handler(get_create_plan_conversation())
    app.add_handler(get_delete_plan_conversation())
    app.add_handler(get_user_plan_conversation())

    # ── Register Command Handlers ───────────────────────────
    app.add_handler(CommandHandler("start", start_handler))

    # ── Register Button Handlers (ReplyKeyboard) ────────────
    app.add_handler(MessageHandler(filters.Regex(f"^{BTN_PROFILE}$"), profile_handler))
    app.add_handler(MessageHandler(filters.Regex(f"^{BTN_GET_EMAIL}$"), get_email_handler))
    app.add_handler(MessageHandler(filters.Regex(f"^{BTN_DIRECT_LINK}$"), direct_link_handler))
    app.add_handler(MessageHandler(filters.Regex(f"^{BTN_TV_ACTIVATION}$"), tv_activation_handler))
    app.add_handler(MessageHandler(filters.Regex(f"^{BTN_SUPPORT}$"), support_handler))

    # ── Admin: ReplyKeyboard entry → opens inline panel ─────
    app.add_handler(MessageHandler(filters.Regex(f"^{BTN_ADMIN_PANEL}$"), admin_panel_handler))

    # ── Admin: Inline button callbacks ──────────────────────
    app.add_handler(CallbackQueryHandler(admin_callback_handler, pattern=r"^admin:"))

    # ── Start Polling ───────────────────────────────────────
    print("🚀 Bot is running! Press Ctrl+C to stop.")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
