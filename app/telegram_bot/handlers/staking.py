from decimal import Decimal
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import async_session_maker
from app.services.staking_engine import get_user_stakes, create_admin_stake


AMOUNTS = [10, 25, 50, 100]
DAYS_OPTIONS = [7, 14, 30]
APY_OPTIONS = [8, 12, 18]


async def _build_staking_message(positions):
    if not positions:
        return (
            "You have no active staking positions yet.\n"
            "Use 'Open New Stake' to create your first position."
        )

    lines = ["Your staking positions:\n"]
    for pos in positions:
        status = "Active" if pos.status == "active" else "Closed"
        created_str = pos.created_at.strftime("%Y-%m-%d") if pos.created_at else "-"
        unlock_str = pos.unlock_at.strftime("%Y-%m-%d") if pos.unlock_at else "-"

        lines.append(
            f"Amount: {pos.amount:.2f} SLH\n"
            f"Days: {pos.days}\n"
            f"APY: {pos.apy:.1f}%\n"
            f"Opened: {created_str}\n"
            f"Unlocks: {unlock_str}\n"
            f"Status: {status}\n"
            "-------------------------"
        )

    return "\n".join(lines)


def _main_keyboard():
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("Refresh", callback_data="stake_refresh"),
                InlineKeyboardButton("Open New Stake", callback_data="stake_open"),
            ]
        ]
    )


def _amount_keyboard():
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(f"{amt} SLH", callback_data=f"stake_amount_{amt}")
                for amt in AMOUNTS[:2]
            ],
            [
                InlineKeyboardButton(f"{amt} SLH", callback_data=f"stake_amount_{amt}")
                for amt in AMOUNTS[2:]
            ],
            [InlineKeyboardButton("Cancel", callback_data="stake_cancel")],
        ]
    )


def _days_keyboard():
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(f"{d} days", callback_data=f"stake_days_{d}")
                for d in DAYS_OPTIONS
            ],
            [InlineKeyboardButton("Cancel", callback_data="stake_cancel")],
        ]
    )


def _apy_keyboard():
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(f"{apy}%", callback_data=f"stake_apy_{apy}")
                for apy in APY_OPTIONS
            ],
            [InlineKeyboardButton("Cancel", callback_data="stake_cancel")],
        ]
    )


def _confirm_keyboard():
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("Confirm", callback_data="stake_confirm"),
                InlineKeyboardButton("Cancel", callback_data="stake_cancel"),
            ]
        ]
    )


async def staking(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.effective_user.id

    async with async_session_maker() as session:
        positions = await get_user_stakes(session, telegram_id)

    text = await _build_staking_message(positions)
    await update.message.reply_text(text, reply_markup=_main_keyboard())


async def staking_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    telegram_id = query.from_user.id
    data = query.data or ""

    # Refresh
    if data == "stake_refresh":
        async with async_session_maker() as session:
            positions = await get_user_stakes(session, telegram_id)
        text = await _build_staking_message(positions)

        try:
            await query.edit_message_text(text, reply_markup=_main_keyboard())
        except Exception as e:
            if "Message is not modified" not in str(e):
                raise
        return

    # Cancel
    if data == "stake_cancel":
        async with async_session_maker() as session:
            positions = await get_user_stakes(session, telegram_id)
        text = await _build_staking_message(positions)

        try:
            await query.edit_message_text(text, reply_markup=_main_keyboard())
        except Exception as e:
            if "Message is not modified" not in str(e):
                raise

        context.user_data.clear()
        return

    # Open new stake
    if data == "stake_open":
        context.user_data.clear()
        await query.edit_message_text(
            "Choose stake amount:", reply_markup=_amount_keyboard()
        )
        return

    # Amount selected
    if data.startswith("stake_amount_"):
        amount = int(data.split("_")[-1])
        context.user_data["stake_amount"] = amount

        await query.edit_message_text(
            f"Amount selected: {amount} SLH\nNow choose duration:",
            reply_markup=_days_keyboard()
        )
        return

    # Days selected
    if data.startswith("stake_days_"):
        days = int(data.split("_")[-1])
        context.user_data["stake_days"] = days

        await query.edit_message_text(
            f"Duration selected: {days} days\nNow choose APY:",
            reply_markup=_apy_keyboard()
        )
        return

    # APY selected
    if data.startswith("stake_apy_"):
        apy = int(data.split("_")[-1])
        context.user_data["stake_apy"] = apy

        amount = context.user_data.get("stake_amount")
        days = context.user_data.get("stake_days")

        await query.edit_message_text(
            f"Confirm your stake:\n\n"
            f"Amount: {amount} SLH\n"
            f"Days: {days}\n"
            f"APY: {apy}%",
            reply_markup=_confirm_keyboard()
        )
        return

    # Confirm stake
    if data == "stake_confirm":
        amount = context.user_data.get("stake_amount")
        days = context.user_data.get("stake_days")
        apy = context.user_data.get("stake_apy")

        async with async_session_maker() as session:
            await create_admin_stake(session, telegram_id, amount, days, apy)

        context.user_data.clear()

        await query.edit_message_text(
            "Your stake has been created successfully!",
            reply_markup=_main_keyboard()
        )
        return
