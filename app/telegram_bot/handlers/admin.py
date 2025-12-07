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
            await update.effective_message.reply_text("⛔ הפקודה זמינה רק למנהל המערכת.")
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
        f"🛠 לוח בקרה  GATE BOTSHOP\n\n"
        f"• משתמשים רשומים: {total_users}\n"
        f"• ארנקים פעילים: {total_wallets}\n"
        f"• תוכניות חיסכון פעילות: {active_stakes}"
    )


async def admin_tvl(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _ensure_admin(update):
        return

    try:
        balance_ton = await get_treasury_balance_ton()
    except:
        balance_ton = None

    if balance_ton is None:
        await update.effective_message.reply_text("🏦 קופת TON לא מוגדרת עדיין.")
    else:
        await update.effective_message.reply_text(f"🏦 יתרת קופה: {balance_ton} TON")
