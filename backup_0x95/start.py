from typing import Tuple

from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session_maker
from app.models.users import User
from app.models.wallets import Wallet


async def _get_or_create_user_and_wallet(
    session: AsyncSession, telegram_id: int
) -> Tuple[User, Wallet]:
    user = (
        await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
    ).scalar_one_or_none()

    if not user:
        user = User(telegram_id=telegram_id)
        session.add(user)
        await session.flush()

    wallet = (
        await session.execute(
            select(Wallet).where(Wallet.user_id == user.id)
        )
    ).scalar_one_or_none()

    if not wallet:
        wallet = Wallet(user_id=user.id)
        session.add(wallet)

    await session.commit()
    return user, wallet


def _build_keyboard(mode: str) -> ReplyKeyboardMarkup:
    row1 = [KeyboardButton("/wallet"), KeyboardButton("/settings")]
    row2 = [KeyboardButton("/stake"), KeyboardButton("/ai")]
    return ReplyKeyboardMarkup([row1, row2], resize_keyboard=True)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.effective_user:
        return

    telegram_id = update.effective_user.id

    async with async_session_maker() as session:
        user, wallet = await _get_or_create_user_and_wallet(session, telegram_id)

    text = (
        "ברוך הבא לGATE BOTSHOP AI 🚀\n\n"
        "כאן תקבל:\n"
        "• ניתוחי שוק חכמים\n"
        "• סימולציית מסחר בטוחה\n"
        "• ובהמשך  מסחר אמיתי על TON/DEX, סטייקינג ו-P2P.\n\n"
        "התחל מעקב דרך /wallet או עדכן הגדרות דרך /settings."
    )

    kb = _build_keyboard(user.investment_mode or "noncustodial")
    await update.effective_message.reply_text(text, reply_markup=kb)
