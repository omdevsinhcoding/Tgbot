"""
IMAP Manager — admin can add, list, delete IMAP accounts
and assign/remove them from users.
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    filters,
)

from database.connection import get_pool
from keyboards.admin_menu import get_admin_menu

# Conversation states
IMAP_EMAIL, IMAP_PASSWORD, IMAP_HOST, IMAP_PORT, IMAP_LABEL = range(20, 25)
IMAP_DELETE_ID = 25
IMAP_ASSIGN_USER_ID, IMAP_ASSIGN_ACCOUNT_ID = 26, 27
IMAP_UNASSIGN_USER_ID, IMAP_UNASSIGN_SELECTION = 28, 29


def get_imap_menu() -> InlineKeyboardMarkup:
    """IMAP management inline keyboard."""
    keyboard = [
        [InlineKeyboardButton("➕ Add IMAP Account", callback_data="imap:add")],
        [InlineKeyboardButton("📄 List IMAP Accounts", callback_data="imap:list")],
        [InlineKeyboardButton("🗑️ Delete IMAP Account", callback_data="imap:delete")],
        [
            InlineKeyboardButton("🔗 Assign to User", callback_data="imap:assign"),
            InlineKeyboardButton("❌ Unassign", callback_data="imap:unassign"),
        ],
        [InlineKeyboardButton("🔙 Back to Admin", callback_data="admin:panel")],
    ]
    return InlineKeyboardMarkup(keyboard)


# ═══════════════════════════════════════════════════════════
# CALLBACK ROUTER
# ═══════════════════════════════════════════════════════════

async def imap_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Route all imap: callbacks."""
    query = update.callback_query
    await query.answer()

    from utils.helpers import is_user_admin
    if not await is_user_admin(query.from_user.id):
        await query.answer("⛔ Access denied.", show_alert=True)
        return

    data = query.data

    if data == "imap:menu":
        await query.message.edit_text(
            "📧 *IMAP Account Manager*\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            "Manage IMAP email accounts and assign them to users:",
            parse_mode="Markdown",
            reply_markup=get_imap_menu(),
        )

    elif data == "imap:list":
        await list_imap_accounts_callback(update, context)


async def list_imap_accounts_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List all IMAP accounts with assignment count."""
    query = update.callback_query
    pool = await get_pool()

    async with pool.acquire() as conn:
        accounts = await conn.fetch("""
            SELECT ia.*,
                   COUNT(uia.id) AS user_count
            FROM imap_accounts ia
            LEFT JOIN user_imap_assignments uia ON ia.id = uia.imap_account_id
            GROUP BY ia.id
            ORDER BY ia.id ASC
        """)

    if not accounts:
        await query.message.edit_text(
            "📧 *No IMAP accounts yet.*\n\n"
            "Add one using ➕ Add IMAP Account.",
            parse_mode="Markdown",
            reply_markup=get_imap_menu(),
        )
        return

    text = "📧 *IMAP Accounts*\n━━━━━━━━━━━━━━━━━━\n"
    for a in accounts:
        status = "✅" if a["is_active"] else "❌"
        text += (
            f"\n🆔 *ID:* {a['id']}\n"
            f"📧 *{a['email']}*\n"
            f"🏷️ Label: {a['label'] or 'N/A'}\n"
            f"🖥️ {a['host']}:{a['port']}\n"
            f"👥 Assigned to: {a['user_count']} users\n"
            f"{status} {'Active' if a['is_active'] else 'Inactive'}\n"
            f"━━━━━━━━━━━━━━━━━━\n"
        )

    await query.message.edit_text(
        text,
        parse_mode="Markdown",
        reply_markup=get_imap_menu(),
    )


# ═══════════════════════════════════════════════════════════
# ADD IMAP ACCOUNT (5-step conversation)
# ═══════════════════════════════════════════════════════════

async def add_imap_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 1: Ask for email address."""
    query = update.callback_query
    await query.message.edit_text(
        "➕ *Add IMAP Account*\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        "*Step 1/5:* Enter the email address:\n\n"
        "Send /cancel to cancel.",
        parse_mode="Markdown",
    )
    return IMAP_EMAIL


async def imap_email_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 2: Save email, ask for password."""
    email = update.message.text.strip()
    if "@" not in email:
        await update.message.reply_text("❌ Enter a valid email address:")
        return IMAP_EMAIL

    context.user_data["imap_email"] = email
    await update.message.reply_text(
        f"✅ Email: *{email}*\n\n"
        "*Step 2/5:* Enter the IMAP password (app password):",
        parse_mode="Markdown",
    )
    return IMAP_PASSWORD


async def imap_password_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 3: Save password, ask for host."""
    context.user_data["imap_password"] = update.message.text.strip()
    await update.message.reply_text(
        "✅ Password saved.\n\n"
        "*Step 3/5:* Enter IMAP host\n"
        "(default: `imap.gmail.com`, just send `.` for default):",
        parse_mode="Markdown",
    )
    return IMAP_HOST


async def imap_host_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 4: Save host, ask for port."""
    text = update.message.text.strip()
    host = "imap.gmail.com" if text == "." else text
    context.user_data["imap_host"] = host
    await update.message.reply_text(
        f"✅ Host: *{host}*\n\n"
        "*Step 4/5:* Enter IMAP port\n"
        "(default: `993`, just send `.` for default):",
        parse_mode="Markdown",
    )
    return IMAP_PORT


async def imap_port_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 5: Save port, ask for label."""
    text = update.message.text.strip()
    if text == ".":
        port = 993
    elif text.isdigit():
        port = int(text)
    else:
        await update.message.reply_text("❌ Enter a valid port number (e.g., 993):")
        return IMAP_PORT

    context.user_data["imap_port"] = port
    await update.message.reply_text(
        f"✅ Port: *{port}*\n\n"
        "*Step 5/5:* Enter a label/nickname for this account\n"
        "(e.g., 'Netflix Main', 'Backup Gmail'):",
        parse_mode="Markdown",
    )
    return IMAP_LABEL


async def imap_label_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Final: Save to database."""
    label = update.message.text.strip()
    data = context.user_data

    pool = await get_pool()
    try:
        async with pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO imap_accounts (email, password, host, port, label)
                VALUES ($1, $2, $3, $4, $5)
                """,
                data["imap_email"],
                data["imap_password"],
                data["imap_host"],
                data["imap_port"],
                label,
            )
    except Exception as e:
        if "duplicate key" in str(e).lower() or "unique" in str(e).lower():
            await update.message.reply_text(
                f"❌ Email *{data['imap_email']}* already exists!",
                parse_mode="Markdown",
                reply_markup=get_imap_menu(),
            )
        else:
            await update.message.reply_text(f"❌ Error: {e}", reply_markup=get_imap_menu())

        _cleanup_imap_data(context)
        return ConversationHandler.END

    await update.message.reply_text(
        "✅ *IMAP Account added successfully!*\n\n"
        f"📧 *{data['imap_email']}*\n"
        f"🏷️ Label: {label}\n"
        f"🖥️ {data['imap_host']}:{data['imap_port']}",
        parse_mode="Markdown",
        reply_markup=get_imap_menu(),
    )

    _cleanup_imap_data(context)
    return ConversationHandler.END


# ═══════════════════════════════════════════════════════════
# DELETE IMAP ACCOUNT
# ═══════════════════════════════════════════════════════════

async def delete_imap_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ask for IMAP account ID to delete."""
    query = update.callback_query
    pool = await get_pool()

    async with pool.acquire() as conn:
        accounts = await conn.fetch(
            "SELECT id, email, label FROM imap_accounts ORDER BY id ASC"
        )

    if not accounts:
        await query.message.edit_text(
            "📧 No IMAP accounts to delete.",
            reply_markup=get_imap_menu(),
        )
        return ConversationHandler.END

    text = "🗑️ *Delete IMAP Account*\n━━━━━━━━━━━━━━━━━━\n\n"
    for a in accounts:
        text += f"🆔 *{a['id']}* — {a['email']} ({a['label'] or 'no label'})\n"
    text += "\nEnter the *Account ID* to delete:\n\nSend /cancel to cancel."

    await query.message.edit_text(text, parse_mode="Markdown")
    return IMAP_DELETE_ID


async def delete_imap_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Delete the IMAP account by ID."""
    text = update.message.text.strip()
    if not text.isdigit():
        await update.message.reply_text("❌ Enter a valid Account ID:")
        return IMAP_DELETE_ID

    account_id = int(text)
    pool = await get_pool()

    async with pool.acquire() as conn:
        result = await conn.execute(
            "DELETE FROM imap_accounts WHERE id = $1", account_id
        )

    if result == "DELETE 1":
        await update.message.reply_text(
            f"✅ IMAP Account ID *{account_id}* deleted.\n"
            "All user assignments also removed.",
            parse_mode="Markdown",
            reply_markup=get_imap_menu(),
        )
    else:
        await update.message.reply_text(
            f"❌ Account ID *{account_id}* not found.",
            parse_mode="Markdown",
            reply_markup=get_imap_menu(),
        )

    return ConversationHandler.END


# ═══════════════════════════════════════════════════════════
# ASSIGN IMAP TO USER
# ═══════════════════════════════════════════════════════════

async def assign_imap_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 1: Ask for user's Telegram ID."""
    query = update.callback_query
    await query.message.edit_text(
        "🔗 *Assign IMAP to User*\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        "Enter the user's *Telegram ID*:\n\n"
        "Send /cancel to cancel.",
        parse_mode="Markdown",
    )
    return IMAP_ASSIGN_USER_ID


async def assign_user_id_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 2: Validate user, show IMAP accounts."""
    text = update.message.text.strip()
    if not text.isdigit():
        await update.message.reply_text("❌ Enter a valid Telegram ID:")
        return IMAP_ASSIGN_USER_ID

    target_id = int(text)
    pool = await get_pool()

    async with pool.acquire() as conn:
        user = await conn.fetchrow(
            "SELECT * FROM users WHERE telegram_id = $1", target_id
        )

    if not user:
        await update.message.reply_text(
            f"❌ User `{target_id}` not found. They must /start first.",
            parse_mode="Markdown",
        )
        return IMAP_ASSIGN_USER_ID

    context.user_data["imap_assign_target"] = target_id

    # Show available IMAP accounts
    async with pool.acquire() as conn:
        accounts = await conn.fetch(
            "SELECT id, email, label FROM imap_accounts WHERE is_active = TRUE ORDER BY id"
        )

        # Get already assigned
        assigned = await conn.fetch(
            "SELECT imap_account_id FROM user_imap_assignments WHERE telegram_id = $1",
            target_id,
        )

    assigned_ids = {r["imap_account_id"] for r in assigned}

    if not accounts:
        await update.message.reply_text(
            "❌ No active IMAP accounts. Add one first.",
            reply_markup=get_imap_menu(),
        )
        return ConversationHandler.END

    text_msg = (
        f"👤 *User:* `{target_id}` ({user['full_name'] or 'N/A'})\n\n"
        "📧 *Available IMAP Accounts:*\n\n"
    )
    for a in accounts:
        assigned_mark = "✅ (assigned)" if a["id"] in assigned_ids else ""
        text_msg += f"🆔 *{a['id']}* — {a['email']} {assigned_mark}\n"

    text_msg += "\nEnter the *IMAP Account ID* to assign:\nSend /cancel to cancel."

    await update.message.reply_text(text_msg, parse_mode="Markdown")
    return IMAP_ASSIGN_ACCOUNT_ID


async def assign_account_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 3: Assign the IMAP account to the user."""
    text = update.message.text.strip()
    if not text.isdigit():
        await update.message.reply_text("❌ Enter a valid Account ID:")
        return IMAP_ASSIGN_ACCOUNT_ID

    account_id = int(text)
    target_id = context.user_data.get("imap_assign_target")
    admin_id = update.effective_user.id
    pool = await get_pool()

    # Verify account exists
    async with pool.acquire() as conn:
        account = await conn.fetchrow(
            "SELECT * FROM imap_accounts WHERE id = $1 AND is_active = TRUE",
            account_id,
        )

    if not account:
        await update.message.reply_text(
            f"❌ Account ID *{account_id}* not found or inactive.",
            parse_mode="Markdown",
        )
        return IMAP_ASSIGN_ACCOUNT_ID

    # Assign
    try:
        async with pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO user_imap_assignments (telegram_id, imap_account_id, assigned_by)
                VALUES ($1, $2, $3)
                ON CONFLICT (telegram_id, imap_account_id) DO NOTHING
                """,
                target_id, account_id, admin_id,
            )
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}", reply_markup=get_imap_menu())
        context.user_data.pop("imap_assign_target", None)
        return ConversationHandler.END

    await update.message.reply_text(
        f"✅ *IMAP Account assigned!*\n\n"
        f"👤 User: `{target_id}`\n"
        f"📧 Account: *{account['email']}*",
        parse_mode="Markdown",
        reply_markup=get_imap_menu(),
    )

    context.user_data.pop("imap_assign_target", None)
    return ConversationHandler.END


# ═══════════════════════════════════════════════════════════
# UNASSIGN IMAP FROM USER
# ═══════════════════════════════════════════════════════════

async def unassign_imap_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 1: Ask for user's Telegram ID."""
    query = update.callback_query
    await query.message.edit_text(
        "❌ *Unassign IMAP from User*\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        "Enter the user's *Telegram ID*:\n\n"
        "Send /cancel to cancel.",
        parse_mode="Markdown",
    )
    return IMAP_UNASSIGN_USER_ID


async def unassign_user_id_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 2: Show assigned accounts for this user."""
    text = update.message.text.strip()
    if not text.isdigit():
        await update.message.reply_text("❌ Enter a valid Telegram ID:")
        return IMAP_UNASSIGN_USER_ID

    target_id = int(text)
    pool = await get_pool()

    async with pool.acquire() as conn:
        assignments = await conn.fetch(
            """
            SELECT uia.id AS assignment_id, ia.id AS account_id, ia.email, ia.label
            FROM user_imap_assignments uia
            JOIN imap_accounts ia ON uia.imap_account_id = ia.id
            WHERE uia.telegram_id = $1
            ORDER BY uia.assigned_at
            """,
            target_id,
        )

    if not assignments:
        await update.message.reply_text(
            f"❌ User `{target_id}` has no IMAP accounts assigned.",
            parse_mode="Markdown",
            reply_markup=get_imap_menu(),
        )
        return ConversationHandler.END

    context.user_data["imap_unassign_target"] = target_id

    text_msg = f"👤 *User:* `{target_id}`\n\n📧 *Assigned IMAP Accounts:*\n\n"
    for a in assignments:
        text_msg += f"🆔 *{a['account_id']}* — {a['email']} ({a['label'] or 'no label'})\n"

    text_msg += "\nEnter the *IMAP Account ID* to unassign:\nSend *0* to remove ALL.\nSend /cancel to cancel."

    await update.message.reply_text(text_msg, parse_mode="Markdown")
    return IMAP_UNASSIGN_SELECTION


async def unassign_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 3: Remove the assignment."""
    text = update.message.text.strip()
    if not text.isdigit():
        await update.message.reply_text("❌ Enter a valid Account ID (or 0 for all):")
        return IMAP_UNASSIGN_SELECTION

    choice = int(text)
    target_id = context.user_data.get("imap_unassign_target")
    pool = await get_pool()

    if choice == 0:
        # Remove all
        async with pool.acquire() as conn:
            await conn.execute(
                "DELETE FROM user_imap_assignments WHERE telegram_id = $1",
                target_id,
            )
        await update.message.reply_text(
            f"✅ All IMAP accounts removed from user `{target_id}`.",
            parse_mode="Markdown",
            reply_markup=get_imap_menu(),
        )
    else:
        async with pool.acquire() as conn:
            result = await conn.execute(
                "DELETE FROM user_imap_assignments WHERE telegram_id = $1 AND imap_account_id = $2",
                target_id, choice,
            )

        if result == "DELETE 1":
            await update.message.reply_text(
                f"✅ IMAP Account *{choice}* removed from user `{target_id}`.",
                parse_mode="Markdown",
                reply_markup=get_imap_menu(),
            )
        else:
            await update.message.reply_text(
                f"❌ Assignment not found.",
                reply_markup=get_imap_menu(),
            )

    context.user_data.pop("imap_unassign_target", None)
    return ConversationHandler.END


# ═══════════════════════════════════════════════════════════
# CANCEL + CLEANUP
# ═══════════════════════════════════════════════════════════

def _cleanup_imap_data(context: ContextTypes.DEFAULT_TYPE):
    """Remove temp IMAP data from user_data."""
    for key in list(context.user_data.keys()):
        if key.startswith("imap_"):
            del context.user_data[key]


async def cancel_imap_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel any IMAP management action."""
    _cleanup_imap_data(context)
    await update.message.reply_text(
        "❌ Action cancelled.",
        reply_markup=get_imap_menu(),
    )
    return ConversationHandler.END


# ═══════════════════════════════════════════════════════════
# CONVERSATION HANDLERS
# ═══════════════════════════════════════════════════════════

def get_add_imap_conversation() -> ConversationHandler:
    """5-step conversation to add an IMAP account."""
    return ConversationHandler(
        entry_points=[
            CallbackQueryHandler(add_imap_start, pattern=r"^imap:add$"),
        ],
        states={
            IMAP_EMAIL: [
                CommandHandler("cancel", cancel_imap_action),
                MessageHandler(filters.TEXT & ~filters.COMMAND, imap_email_received),
            ],
            IMAP_PASSWORD: [
                CommandHandler("cancel", cancel_imap_action),
                MessageHandler(filters.TEXT & ~filters.COMMAND, imap_password_received),
            ],
            IMAP_HOST: [
                CommandHandler("cancel", cancel_imap_action),
                MessageHandler(filters.TEXT & ~filters.COMMAND, imap_host_received),
            ],
            IMAP_PORT: [
                CommandHandler("cancel", cancel_imap_action),
                MessageHandler(filters.TEXT & ~filters.COMMAND, imap_port_received),
            ],
            IMAP_LABEL: [
                CommandHandler("cancel", cancel_imap_action),
                MessageHandler(filters.TEXT & ~filters.COMMAND, imap_label_received),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel_imap_action)],
        per_message=False,
    )


def get_delete_imap_conversation() -> ConversationHandler:
    """Conversation to delete an IMAP account."""
    return ConversationHandler(
        entry_points=[
            CallbackQueryHandler(delete_imap_start, pattern=r"^imap:delete$"),
        ],
        states={
            IMAP_DELETE_ID: [
                CommandHandler("cancel", cancel_imap_action),
                MessageHandler(filters.TEXT & ~filters.COMMAND, delete_imap_confirm),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel_imap_action)],
        per_message=False,
    )


def get_assign_imap_conversation() -> ConversationHandler:
    """Conversation to assign IMAP account to user."""
    return ConversationHandler(
        entry_points=[
            CallbackQueryHandler(assign_imap_start, pattern=r"^imap:assign$"),
        ],
        states={
            IMAP_ASSIGN_USER_ID: [
                CommandHandler("cancel", cancel_imap_action),
                MessageHandler(filters.TEXT & ~filters.COMMAND, assign_user_id_received),
            ],
            IMAP_ASSIGN_ACCOUNT_ID: [
                CommandHandler("cancel", cancel_imap_action),
                MessageHandler(filters.TEXT & ~filters.COMMAND, assign_account_selected),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel_imap_action)],
        per_message=False,
    )


def get_unassign_imap_conversation() -> ConversationHandler:
    """Conversation to unassign IMAP account from user."""
    return ConversationHandler(
        entry_points=[
            CallbackQueryHandler(unassign_imap_start, pattern=r"^imap:unassign$"),
        ],
        states={
            IMAP_UNASSIGN_USER_ID: [
                CommandHandler("cancel", cancel_imap_action),
                MessageHandler(filters.TEXT & ~filters.COMMAND, unassign_user_id_received),
            ],
            IMAP_UNASSIGN_SELECTION: [
                CommandHandler("cancel", cancel_imap_action),
                MessageHandler(filters.TEXT & ~filters.COMMAND, unassign_selection),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel_imap_action)],
        per_message=False,
    )
