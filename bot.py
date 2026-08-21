"""
Bot Entry Point — initializes the bot, database, and registers all handlers.
"""

from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

from config import (
    BOT_TOKEN,
    BTN_CHECK_HOUSE, BTN_CHECK_TEMP,
    BTN_PROFILE, BTN_HELP, BTN_ADMIN_PANEL,
    TICKET_RAISE,
)

# Database
from database.connection import create_pool, close_pool
from database.models import init_database

# Handlers
from handlers.start import start_handler
from handlers.profile import profile_handler
from handlers.get_email import check_household_handler, check_temp_handler
from handlers.support import support_handler

# Admin Handlers
from handlers.admin.panel import admin_panel_handler, admin_callback_handler
from handlers.admin.welcome_editor import get_welcome_editor_conversation
from handlers.admin.plan_manager import (
    get_create_plan_conversation,
    get_delete_plan_conversation,
)
from handlers.admin.user_plan import get_user_plan_conversation

# IMAP Handlers
from handlers.admin.imap_manager import (
    imap_callback_handler,
    get_add_imap_conversation,
    get_delete_imap_conversation,
    get_assign_imap_conversation,
    get_unassign_imap_conversation,
)


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
        print("❌ BOT_TOKEN not set! Fill in your .env file.")
        return

    # ── Build Application ───────────────────────────────────
    app = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .post_init(post_init)
        .post_shutdown(post_shutdown)
        .build()
    )

    # ── ConversationHandlers FIRST (higher priority) ────────
    app.add_handler(get_welcome_editor_conversation())
    app.add_handler(get_create_plan_conversation())
    app.add_handler(get_delete_plan_conversation())
    app.add_handler(get_user_plan_conversation())
    app.add_handler(get_add_imap_conversation())
    app.add_handler(get_delete_imap_conversation())
    app.add_handler(get_assign_imap_conversation())
    app.add_handler(get_unassign_imap_conversation())

    # ── Command Handlers ────────────────────────────────────
    app.add_handler(CommandHandler("start", start_handler))

    # ── User Button Handlers (ReplyKeyboard) ────────────────
    app.add_handler(MessageHandler(
        filters.Regex(f"^{BTN_CHECK_HOUSE}$"), check_household_handler
    ))
    app.add_handler(MessageHandler(
        filters.Regex(f"^{BTN_CHECK_TEMP}$"), check_temp_handler
    ))
    app.add_handler(MessageHandler(
        filters.Regex(f"^{BTN_PROFILE}$"), profile_handler
    ))
    app.add_handler(MessageHandler(
        filters.Regex(f"^{BTN_HELP}$"), support_handler
    ))

    # ── Admin Panel: ReplyKeyboard entry → inline panel ─────
    app.add_handler(MessageHandler(
        filters.Regex(f"^{BTN_ADMIN_PANEL}$"), admin_panel_handler
    ))

    # ── Admin Inline Callbacks ──────────────────────────────
    app.add_handler(CallbackQueryHandler(admin_callback_handler, pattern=r"^admin:"))
    app.add_handler(CallbackQueryHandler(imap_callback_handler, pattern=r"^imap:"))

    # ── Start Polling ───────────────────────────────────────
    print("🚀 Bot is running! Press Ctrl+C to stop.")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
