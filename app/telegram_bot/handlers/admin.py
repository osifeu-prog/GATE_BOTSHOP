أ—ع؛ط¢آ»ط¢طںfrom decimal import Decimal

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
            await update.effective_message.reply_text("أ—â€™أ¢â‚¬ط›أ¢â‚¬â€Œ أ—آ³أ¢â‚¬â€Œأ—آ³أ¢â€ڑع¾أ—آ³ط¢آ§أ—آ³أ¢â‚¬آ¢أ—آ³أ¢â‚¬إ“أ—آ³أ¢â‚¬â€Œ أ—آ³أ¢â‚¬â€œأ—آ³ط¢â€چأ—آ³أ¢â€‍آ¢أ—آ³ط¢آ أ—آ³أ¢â‚¬â€Œ أ—آ³ط¢آ¨أ—آ³ط¢آ§ أ—آ³ط¢إ“أ—آ³ط¢â€چأ—آ³ط¢آ أ—آ³أ¢â‚¬â€Œأ—آ³ط¢إ“ أ—آ³أ¢â‚¬â€Œأ—آ³ط¢â€چأ—آ³ط¢آ¢أ—آ³ط¢آ¨أ—آ³أ¢â‚¬ط›أ—آ³ط£â€”.")
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
        f"أ—آ ط¢ع؛أ¢â‚¬ط›ط¢آ  أ—آ³ط¢إ“أ—آ³أ¢â‚¬آ¢أ—آ³أ¢â‚¬â€‌ أ—آ³أ¢â‚¬ع©أ—آ³ط¢آ§أ—آ³ط¢آ¨أ—آ³أ¢â‚¬â€Œ  GATE BOTSHOP\n\n"
        f"أ—â€™أ¢â€ڑآ¬ط¢آ¢ أ—آ³ط¢â€چأ—آ³ط¢آ©أ—آ³ط£â€”أ—آ³ط¢â€چأ—آ³ط¢آ©أ—آ³أ¢â€‍آ¢أ—آ³ط¢â€Œ أ—آ³ط¢آ¨أ—آ³ط¢آ©أ—آ³أ¢â‚¬آ¢أ—آ³ط¢â€چأ—آ³أ¢â€‍آ¢أ—آ³ط¢â€Œ: {total_users}\n"
        f"أ—â€™أ¢â€ڑآ¬ط¢آ¢ أ—آ³ط¢ع¯أ—آ³ط¢آ¨أ—آ³ط¢آ أ—آ³ط¢آ§أ—آ³أ¢â€‍آ¢أ—آ³ط¢â€Œ أ—آ³أ¢â€ڑع¾أ—آ³ط¢آ¢أ—آ³أ¢â€‍آ¢أ—آ³ط¢إ“أ—آ³أ¢â€‍آ¢أ—آ³ط¢â€Œ: {total_wallets}\n"
        f"أ—â€™أ¢â€ڑآ¬ط¢آ¢ أ—آ³ط£â€”أ—آ³أ¢â‚¬آ¢أ—آ³أ¢â‚¬ط›أ—آ³ط¢آ أ—آ³أ¢â€‍آ¢أ—آ³أ¢â‚¬آ¢أ—آ³ط£â€” أ—آ³أ¢â‚¬â€‌أ—آ³أ¢â€‍آ¢أ—آ³ط¢طŒأ—آ³أ¢â‚¬ط›أ—آ³أ¢â‚¬آ¢أ—آ³ط¢ع؛ أ—آ³أ¢â€ڑع¾أ—آ³ط¢آ¢أ—آ³أ¢â€‍آ¢أ—آ³ط¢إ“أ—آ³أ¢â‚¬آ¢أ—آ³ط£â€”: {active_stakes}"
    )


async def admin_tvl(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _ensure_admin(update):
        return

    try:
        balance_ton = await get_treasury_balance_ton()
    except:
        balance_ton = None

    if balance_ton is None:
        await update.effective_message.reply_text("أ—آ ط¢ع؛ط¢عˆط¢آ¦ أ—آ³ط¢آ§أ—آ³أ¢â‚¬آ¢أ—آ³أ¢â€ڑع¾أ—آ³ط£â€” TON أ—آ³ط¢إ“أ—آ³ط¢ع¯ أ—آ³ط¢â€چأ—آ³أ¢â‚¬آ¢أ—آ³أ¢â‚¬â„¢أ—آ³أ¢â‚¬إ“أ—آ³ط¢آ¨أ—آ³ط£â€” أ—آ³ط¢آ¢أ—آ³أ¢â‚¬إ“أ—آ³أ¢â€‍آ¢أ—آ³أ¢â€‍آ¢أ—آ³ط¢ع؛.")
    else:
        await update.effective_message.reply_text(f"أ—آ ط¢ع؛ط¢عˆط¢آ¦ أ—آ³أ¢â€‍آ¢أ—آ³ط£â€”أ—آ³ط¢آ¨أ—آ³ط£â€” أ—آ³ط¢آ§أ—آ³أ¢â‚¬آ¢أ—آ³أ¢â€ڑع¾أ—آ³أ¢â‚¬â€Œ: {balance_ton} TON")



