"""
User Plan Manager — admin assigns/removes plans from users.
Uses ConversationHandler triggered by inline callback.
"""

from datetime import datetime, timedelta

from telegram import Update
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
from keyboards.admin_menu import get_admin_menu

# Conversation states
USER_TELEGRAM_ID, SELECT_PLAN = range(2)


async def start_user_plan_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Step 1: Ask for user's Telegram ID (triggered by inline button).
    """
    query = update.callback_query

    await query.message.edit_text(
        "👥 *Manage User Plans*\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        "Enter the user's *Telegram ID* to assign a plan:\n\n"
        "Send /cancel to cancel.",
        parse_mode="Markdown",
    )
    return USER_TELEGRAM_ID


async def user_id_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 2: Validate Telegram ID, show available plans."""
    text = update.message.text
    if not text.isdigit():
        await update.message.reply_text("❌ Please enter a valid Telegram ID (numbers only):")
        return USER_TELEGRAM_ID

    target_user_id = int(text)
    pool = await get_pool()

    # Check if user exists
    async with pool.acquire() as conn:
        user = await conn.fetchrow(
            "SELECT * FROM users WHERE telegram_id = $1",
            target_user_id,
        )

    if not user:
        await update.message.reply_text(
            f"❌ User with Telegram ID `{target_user_id}` not found.\n"
            "The user must /start the bot first.",
            parse_mode="Markdown",
        )
        return USER_TELEGRAM_ID

    # Save target user ID
    context.user_data["target_user_id"] = target_user_id

    # Show available plans
    plans = await get_active_plans()
    if not plans:
        await update.message.reply_text(
            "❌ No active plans available. Create one first.",
            reply_markup=get_admin_menu(),
        )
        return ConversationHandler.END

    # Show user info + plans
    user_info = (
        f"👤 *User Found:*\n"
        f"🆔 ID: `{user['telegram_id']}`\n"
        f"📛 Name: {user['full_name'] or 'N/A'}\n"
        f"📦 Current Plan: {user['plan_id'] or 'None'}\n\n"
    )

    plans_text = "📦 *Available Plans:*\n\n"
    for p in plans:
        plans_text += f"🆔 *{p['id']}* — {p['name']} ({p['duration_days']} days, ₹{p['price']})\n"

    plans_text += (
        "\n\nEnter the *Plan ID* to assign to this user.\n"
        "Send *0* to remove the current plan.\n"
        "Send /cancel to cancel."
    )

    await update.message.reply_text(
        user_info + plans_text,
        parse_mode="Markdown",
    )
    return SELECT_PLAN


async def plan_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 3: Assign the selected plan to the user."""
    text = update.message.text
    if not text.isdigit():
        await update.message.reply_text("❌ Please enter a valid Plan ID:")
        return SELECT_PLAN

    plan_id = int(text)
    target_user_id = context.user_data.get("target_user_id")
    pool = await get_pool()

    if plan_id == 0:
        # Remove plan from user
        async with pool.acquire() as conn:
            await conn.execute(
                "UPDATE users SET plan_id = NULL, plan_expires_at = NULL WHERE telegram_id = $1",
                target_user_id,
            )
        await update.message.reply_text(
            f"✅ Plan removed from user `{target_user_id}`.",
            parse_mode="Markdown",
            reply_markup=get_admin_menu(),
        )
    else:
        # Verify plan exists
        async with pool.acquire() as conn:
            plan = await conn.fetchrow(
                "SELECT * FROM plans WHERE id = $1 AND is_active = TRUE",
                plan_id,
            )

        if not plan:
            await update.message.reply_text(
                f"❌ Plan ID *{plan_id}* not found or inactive.",
                parse_mode="Markdown",
            )
            return SELECT_PLAN

        # Assign plan with expiry
        expires_at = datetime.now() + timedelta(days=plan["duration_days"])

        async with pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE users
                SET plan_id = $1, plan_expires_at = $2
                WHERE telegram_id = $3
                """,
                plan_id, expires_at, target_user_id,
            )

        await update.message.reply_text(
            f"✅ *Plan assigned successfully!*\n\n"
            f"👤 User: `{target_user_id}`\n"
            f"📦 Plan: *{plan['name']}*\n"
            f"⏳ Expires: {expires_at.strftime('%d %b %Y, %I:%M %p')}",
            parse_mode="Markdown",
            reply_markup=get_admin_menu(),
        )

    # Cleanup
    context.user_data.pop("target_user_id", None)
    return ConversationHandler.END


async def cancel_user_plan_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel user plan management."""
    context.user_data.pop("target_user_id", None)
    await update.message.reply_text(
        "❌ Action cancelled.",
        reply_markup=get_admin_menu(),
    )
    return ConversationHandler.END


def get_user_plan_conversation() -> ConversationHandler:
    """Build ConversationHandler for user plan management."""
    return ConversationHandler(
        entry_points=[
            CallbackQueryHandler(
                start_user_plan_callback,
                pattern=r"^admin:user_plans$",
            ),
        ],
        states={
            USER_TELEGRAM_ID: [
                CommandHandler("cancel", cancel_user_plan_action),
                MessageHandler(filters.TEXT & ~filters.COMMAND, user_id_received),
            ],
            SELECT_PLAN: [
                CommandHandler("cancel", cancel_user_plan_action),
                MessageHandler(filters.TEXT & ~filters.COMMAND, plan_selected),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel_user_plan_action)],
        per_message=False,
    )
