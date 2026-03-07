from telegram import Update
from telegram.ext import ContextTypes
from sqlalchemy import select

from app.database import async_session_maker
from app.models.users import User as UserModel
from app.models.wallets import Wallet


async def set_bsc_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user:
        return

    telegram_id = update.effective_user.id

    if not context.args:
        await update.message.reply_text("??? ??? ????? BSC:\n/set_bsc_address 0x1234...")
        return

    address = context.args[0].strip()

    if not address.startswith("0x") or len(address) != 42:
        await update.message.reply_text("????? ?? ?????. ????? ????? ?????? 0x...")
        return

    async with async_session_maker() as session:
        user = (
            await session.execute(
                select(UserModel).where(UserModel.telegram_id == telegram_id)
            )
        ).scalar_one_or_none()

        if not user:
            user = UserModel(telegram_id=telegram_id)
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

        wallet.bsc_address = address
        await session.commit()

    await update.message.reply_text(f"????? BSC ?????? ??????:\n{address}")



