from decimal import Decimal

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session_maker
from app.services.staking_engine import get_user_stakes, create_admin_stake


AMOUNTS = [10, 25, 50, 100]
DAYS_OPTIONS = [7, 14, 30]
APY_OPTIONS = [8, 12, 18]


async def _build_staking_message(positions):
    if not positions:
        text = (
            "You have no active staking positions yet.\n"
            "Use 'Open New Stake' to create your first position."
        )
        return text

    lines = ["Your staking positions:\n"]
    for pos in positions:
        status = "Active" if getattr(pos, "status", "") == "active" else "Closed"
        amount = getattr(pos, "amount", 0)
        days = getattr(pos, "days", 0)
        apy = getattr(pos, "apy", 0.0)
        created_at = getattr(pos, "created_at", None)
        unlock_at = getattr(pos, "unlock_at", None)

        created_str = created_at.strftime("%Y-%m-%d") if created_at else "-"
        unlock_str = unlock_at.strftime("%Y-%m-%d") if unlock_at else "-"

        lines.append(
            f"Amount: {amount:.2f} SLH\n"
            f"Days: {days}\n"
            f"APY: {apy:.1f}%\n"
            f"Opened: {created_str}\n"
            f"Unlocks: {unlock_str}\n"
            f"Status: {status}\n"
            "-------------------------"
        )
    return "\n".join(lines)


def _main_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("Refresh", callback_data="stake_refresh"),
            InlineKeyboardButton("Open New Stake", callback_data="stake_open"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def _amount_keyboard():
    keyboard = [
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
    return InlineKeyboardMarkup(keyboard)


def _days_keyboard():
    keyboard = [
        [
            InlineKeyboardButton(f"{d} days", callback_data=f"stake_days_{d}")
            for d in DAYS_OPTIONS
        ],
        [InlineKeyboardButton("Cancel", callback_data="stake_cancel")],
    ]
    return InlineKeyboardMarkup(keyboard)


def _apy_keyboard():
    keyboard = [
        [
            InlineKeyboardButton(f"{apy}%", callback_data=f"stake_apy_{apy}")
            for apy in APY_OPTIONS
        ],
        [InlineKeyboardButton("Cancel", callback_data="stake_cancel")],
    ]
    return InlineKeyboardMarkup(keyboard)


def _confirm_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("Confirm", callback_data="stake_confirm"),
            InlineKeyboardButton("Cancel", callback_data="stake_cancel"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


async def staking(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.effective_user.id

    async with async_session_maker() as session:  # type: AsyncSession
        positions = await get_user_stakes(session, telegram_id)

    text = await _build_staking_message(positions)
    await update.message.reply_text(text, reply_markup=_main_keyboard())


async def staking_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    telegram_id = query.from_user.id
    data = query.data or ""

    # Refresh main view
    if data == "stake_refresh":
        async with async_session_maker() as session:  # type: AsyncSession
            positions = await get_user_stakes(session, telegram_id)
        text = await _build_staking_message(positions)
        await query.edit_message_text(text, reply_markup=_main_keyboard())
        return

    # Cancel flow and go back to main
    if data == "stake_cancel":
        async with async_session_maker() as session:  # type: AsyncSession
            positions = await get_user_stakes(session, telegram_id)
        text = await _build_staking_message(positions)
        await query.edit_message_text(text, reply_markup=_main_keyboard())
        context.user_data.pop("stake_amount", None)
        context.user_data.pop("stake_days", None)
        context.user_data.pop("stake_apy", None)
        return

    # Start new stake flow
    if data == "stake_open":
        context.user_data.pop("stake_amount", None)
        context.user_data.pop("stake_days", None)
        context.user_data.pop("stake_apy", None)
        await query.edit_message_text(
            "Choose stake amount:", reply_markup=_amount_keyboard()
        )
        return

    # Amount selected
    if data.startswith("stake_amount_"):
        try:
            amount = int(data.split("_")[-1])
        except ValueError:
            await query.edit_message_text(
                "Invalid amount selected. Please try again.",
                reply_markup=_amount_keyboard(),
            )
            return

        context.user_data["stake_amount"] = amount
        await query.edit_message_text(
            f"Amount selected: {amount} SLH\nNow choose duration (days):",
            reply_markup=_days_keyboard(),
        )
        return

    # Days selected
    if data.startswith("stake_days_"):
        try:
            days = int(data.split("_")[-1])
        except ValueError:
            await query.edit_message_text(
                "Invalid duration selected. Please try again.",
                reply_markup=_days_keyboard(),
            )
            return

        context.user_data["stake_days"] = days
        await query.edit_message_text(
            f"Duration selected: {days} days\nNow choose APY:",
            reply_markup=_apy_keyboard(),
        )
        return

    # APY selected
    if data.startswith("stake_apy_"):
        try:
            apy = int(data.split("_")[-1])
        except ValueError:
            await query.edit_message_text(
                "Invalid APY selected. Please try again.",
                reply_markup=_apy_keyboard(),
            )
            return

        context.user_data["stake_apy"] = apy

        amount = context.user_data.get("stake_amount")
        days = context.user_data.get("stake_days")

        if amount is None or days is None:
            await query.edit_message_text(
                "Flow state lost. Please start again with /stake.",
                reply_markup=_main_keyboard(),
            )
            context.user_data.pop("stake_amount", None)
            context.user_data.pop("stake_days", None)
            context.user_data.pop("stake_apy", None)
            return

        amount_dec = Decimal(amount)
        apy_dec = Decimal(apy)
        profit = amount_dec * (apy_dec / Decimal(100)) * Decimal(days) / Decimal(365)

        summary = (
            "Please confirm your new staking position:\n\n"
            f"Amount: {amount} SLH\n"
            f"Duration: {days} days\n"
            f"APY: {apy}%\n"
            f"Estimated profit (per period): {profit:.4f} SLH\n\n"
            "Press Confirm to create this staking position."
        )

        await query.edit_message_text(summary, reply_markup=_confirm_keyboard())
        return

    # Confirm and create stake
    if data == "stake_confirm":
        amount = context.user_data.get("stake_amount")
        days = context.user_data.get("stake_days")
        apy = context.user_data.get("stake_apy")

        if amount is None or days is None or apy is None:
            await query.edit_message_text(
                "Flow state lost. Please start again with /stake.",
                reply_markup=_main_keyboard(),
            )
            context.user_data.pop("stake_amount", None)
            context.user_data.pop("stake_days", None)
            context.user_data.pop("stake_apy", None)
            return

        async with async_session_maker() as session:  # type: AsyncSession
            await create_admin_stake(
                session=session,
                telegram_user_id=telegram_id,
                principal_slh=Decimal(amount),
                duration_days=int(days),
                apy_percent=Decimal(apy),
            )
            positions = await get_user_stakes(session, telegram_id)

        context.user_data.pop("stake_amount", None)
        context.user_data.pop("stake_days", None)
        context.user_data.pop("stake_apy", None)

        text = await _build_staking_message(positions)
        await query.edit_message_text(
            "New staking position created successfully.\n\n" + text,
            reply_markup=_main_keyboard(),
        )
        return
