from decimal import Decimal

from telegram import Update
from telegram.ext import ContextTypes
from sqlalchemy import select, func

from app.config import settings
from app.database import async_session_maker
from app.models.users import User
from app.models.wallets import Wallet
from app.models.staking_positions import StakingPosition
from app.services.ton_treasury_service import get_treasury_balance_ton


ADMIN_ID = settings.ADMIN_USER_ID


async def _ensure_admin(update: Update) -> bool:
    user = update.effective_user
    if not user or user.id != ADMIN_ID:
        if update.effective_message:
            await update.effective_message.reply_text("â›” ×”×¤×§×•×“×” ×–×‍×™× ×” ×¨×§ ×œ×‍× ×”×œ ×”×‍×¢×¨×›×ھ.")
        return False
    return True


async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _ensure_admin(update):
        return

    async with async_session_maker() as session:
        total_users = (await session.execute(select(func.count(User.id)))).scalar_one()
        total_wallets = (await session.execute(select(func.count(Wallet.id)))).scalar_one()
        active_stakes = (await session.execute(select(func.count(StakingPosition.id)))).scalar_one()

    await update.effective_message.reply_text(
        f"ًں›  ×œ×•×— ×‘×§×¨×”  GATE BOTSHOP\n\n"
        f"â€¢ ×‍×©×ھ×‍×©×™×‌ ×¨×©×•×‍×™×‌: {total_users}\n"
        f"â€¢ ×گ×¨× ×§×™×‌ ×¤×¢×™×œ×™×‌: {total_wallets}\n"
        f"â€¢ ×ھ×•×›× ×™×•×ھ ×—×™×،×›×•×ں ×¤×¢×™×œ×•×ھ: {active_stakes}"
    )


async def admin_tvl(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _ensure_admin(update):
        return

    try:
        balance_ton = await get_treasury_balance_ton()
    except:
        balance_ton = None

    if balance_ton is None:
        await update.effective_message.reply_text("ًںڈ¦ ×§×•×¤×ھ TON ×œ×گ ×‍×•×’×“×¨×ھ ×¢×“×™×™×ں.")
    else:
        await update.effective_message.reply_text(f"ًںڈ¦ ×™×ھ×¨×ھ ×§×•×¤×”: {balance_ton} TON")

