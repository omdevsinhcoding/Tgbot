"""
Plan Manager — admin can create, list, and delete subscription plans.
Uses ConversationHandler triggered by inline callbacks.
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
from utils.helpers import get_active_plans
from keyboards.admin_menu import get_plan_manager_menu, get_admin_menu

# Conversation states for plan creation
PLAN_NAME, PLAN_DESC, PLAN_DURATION, PLAN_PRICE, PLAN_MAX_EMAILS = range(5)

# Conversation state for plan deletion
PLAN_DELETE_ID = 10


# ═══════════════════════════════════════════════════════════
# CREATE PLAN (multi-step conversation)
# ═══════════════════════════════════════════════════════════

async def start_create_plan_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 1: Ask for plan name (triggered by inline button)."""
    query = update.callback_query

    await query.message.edit_text(
        "➕ *Create New Plan*\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        "*Step 1/5:* Enter the plan name:\n\n"
        "Send /cancel to cancel.",
        parse_mode="Markdown",
    )
    return PLAN_NAME


async def plan_name_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 2: Save name, ask for description."""
    context.user_data["new_plan_name"] = update.message.text
    await update.message.reply_text(
        f"✅ Plan name: *{update.message.text}*\n\n"
        "*Step 2/5:* Enter the plan description:",
        parse_mode="Markdown",
    )
    return PLAN_DESC


async def plan_desc_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 3: Save description, ask for duration."""
    context.user_data["new_plan_desc"] = update.message.text
    await update.message.reply_text(
        "*Step 3/5:* Enter duration in days (e.g., 30):",
        parse_mode="Markdown",
    )
    return PLAN_DURATION


async def plan_duration_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 4: Save duration, ask for price."""
    text = update.message.text
    if not text.isdigit() or int(text) <= 0:
        await update.message.reply_text("❌ Please enter a valid number of days (e.g., 30):")
        return PLAN_DURATION

    context.user_data["new_plan_duration"] = int(text)
    await update.message.reply_text(
        f"✅ Duration: *{text} days*\n\n"
        "*Step 4/5:* Enter the price (e.g., 199.00):",
        parse_mode="Markdown",
    )
    return PLAN_PRICE


async def plan_price_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 5: Save price, ask for max emails."""
    text = update.message.text
    try:
        price = float(text)
        if price < 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text("❌ Please enter a valid price (e.g., 199.00):")
        return PLAN_PRICE

    context.user_data["new_plan_price"] = price
    await update.message.reply_text(
        f"✅ Price: *₹{price:.2f}*\n\n"
        "*Step 5/5:* Enter max emails allowed (e.g., 100):",
        parse_mode="Markdown",
    )
    return PLAN_MAX_EMAILS


async def plan_max_emails_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Final step: Save the plan to the database."""
    text = update.message.text
    if not text.isdigit() or int(text) <= 0:
        await update.message.reply_text("❌ Please enter a valid number (e.g., 100):")
        return PLAN_MAX_EMAILS

    max_emails = int(text)
    data = context.user_data

    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO plans (name, description, duration_days, price, max_emails)
            VALUES ($1, $2, $3, $4, $5)
            """,
            data["new_plan_name"],
            data["new_plan_desc"],
            data["new_plan_duration"],
            data["new_plan_price"],
            max_emails,
        )

    await update.message.reply_text(
        "✅ *Plan created successfully!*\n\n"
        f"📦 *{data['new_plan_name']}*\n"
        f"📝 {data['new_plan_desc']}\n"
        f"⏳ {data['new_plan_duration']} days\n"
        f"💰 ₹{data['new_plan_price']:.2f}\n"
        f"📧 {max_emails} emails",
        parse_mode="Markdown",
        reply_markup=get_plan_manager_menu(),
    )

    # Cleanup temp data
    for key in list(data.keys()):
        if key.startswith("new_plan_"):
            del data[key]

    return ConversationHandler.END


# ═══════════════════════════════════════════════════════════
# LIST PLANS (inline callback, no conversation needed)
# ═══════════════════════════════════════════════════════════

async def list_plans_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show all plans (active + inactive)."""
    query = update.callback_query
    pool = await get_pool()

    async with pool.acquire() as conn:
        plans = await conn.fetch("SELECT * FROM plans ORDER BY id ASC")

    if not plans:
        await query.message.edit_text(
            "📋 *No plans exist yet.*\n\nCreate one using ➕ Create Plan.",
            parse_mode="Markdown",
            reply_markup=get_plan_manager_menu(),
        )
        return

    text = "📋 *All Plans*\n━━━━━━━━━━━━━━━━━━\n"
    for p in plans:
        status = "✅ Active" if p["is_active"] else "❌ Inactive"
        text += (
            f"\n🆔 *ID:* {p['id']}\n"
            f"📦 *{p['name']}*\n"
            f"📝 {p['description']}\n"
            f"⏳ {p['duration_days']} days | 📧 {p['max_emails']} emails\n"
            f"💰 ₹{p['price']} | {status}\n"
            f"━━━━━━━━━━━━━━━━━━\n"
        )

    await query.message.edit_text(
        text,
        parse_mode="Markdown",
        reply_markup=get_plan_manager_menu(),
    )


# ═══════════════════════════════════════════════════════════
# DELETE PLAN (conversation triggered by inline)
# ═══════════════════════════════════════════════════════════

async def start_delete_plan_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ask for the plan ID to delete (triggered by inline button)."""
    query = update.callback_query
    plans = await get_active_plans()

    if not plans:
        await query.message.edit_text(
            "📋 No active plans to delete.",
            reply_markup=get_plan_manager_menu(),
        )
        return ConversationHandler.END

    text = "🗑️ *Delete a Plan*\n━━━━━━━━━━━━━━━━━━\n\n"
    for p in plans:
        text += f"🆔 *{p['id']}* — {p['name']} (₹{p['price']})\n"
    text += "\nEnter the *Plan ID* to deactivate:\n\nSend /cancel to cancel."

    await query.message.edit_text(text, parse_mode="Markdown")
    return PLAN_DELETE_ID


async def delete_plan_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Deactivate the plan by ID."""
    text = update.message.text
    if not text.isdigit():
        await update.message.reply_text("❌ Please enter a valid Plan ID:")
        return PLAN_DELETE_ID

    plan_id = int(text)
    pool = await get_pool()

    async with pool.acquire() as conn:
        result = await conn.execute(
            "UPDATE plans SET is_active = FALSE WHERE id = $1 AND is_active = TRUE",
            plan_id,
        )

    if result == "UPDATE 1":
        await update.message.reply_text(
            f"✅ Plan ID *{plan_id}* has been deactivated.",
            parse_mode="Markdown",
            reply_markup=get_plan_manager_menu(),
        )
    else:
        await update.message.reply_text(
            f"❌ Plan ID *{plan_id}* not found or already inactive.",
            parse_mode="Markdown",
            reply_markup=get_plan_manager_menu(),
        )

    return ConversationHandler.END


# ═══════════════════════════════════════════════════════════
# CANCEL
# ═══════════════════════════════════════════════════════════

async def cancel_plan_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel any plan management action."""
    for key in list(context.user_data.keys()):
        if key.startswith("new_plan_"):
            del context.user_data[key]

    await update.message.reply_text(
        "❌ Action cancelled.",
        reply_markup=get_plan_manager_menu(),
    )
    return ConversationHandler.END


# ═══════════════════════════════════════════════════════════
# CONVERSATION HANDLERS
# ═══════════════════════════════════════════════════════════

def get_create_plan_conversation() -> ConversationHandler:
    """Build ConversationHandler for plan creation (5-step)."""
    return ConversationHandler(
        entry_points=[
            CallbackQueryHandler(start_create_plan_callback, pattern=r"^admin:create_plan$"),
        ],
        states={
            PLAN_NAME: [
                CommandHandler("cancel", cancel_plan_action),
                MessageHandler(filters.TEXT & ~filters.COMMAND, plan_name_received),
            ],
            PLAN_DESC: [
                CommandHandler("cancel", cancel_plan_action),
                MessageHandler(filters.TEXT & ~filters.COMMAND, plan_desc_received),
            ],
            PLAN_DURATION: [
                CommandHandler("cancel", cancel_plan_action),
                MessageHandler(filters.TEXT & ~filters.COMMAND, plan_duration_received),
            ],
            PLAN_PRICE: [
                CommandHandler("cancel", cancel_plan_action),
                MessageHandler(filters.TEXT & ~filters.COMMAND, plan_price_received),
            ],
            PLAN_MAX_EMAILS: [
                CommandHandler("cancel", cancel_plan_action),
                MessageHandler(filters.TEXT & ~filters.COMMAND, plan_max_emails_received),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel_plan_action)],
        per_message=False,
    )


def get_delete_plan_conversation() -> ConversationHandler:
    """Build ConversationHandler for plan deletion."""
    return ConversationHandler(
        entry_points=[
            CallbackQueryHandler(start_delete_plan_callback, pattern=r"^admin:delete_plan$"),
        ],
        states={
            PLAN_DELETE_ID: [
                CommandHandler("cancel", cancel_plan_action),
                MessageHandler(filters.TEXT & ~filters.COMMAND, delete_plan_confirm),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel_plan_action)],
        per_message=False,
    )
