from telegram import Update
from telegram.ext import ContextTypes
from sqlalchemy import select

from app.database import async_session_maker
from app.models.users import User as UserModel
from app.models.wallets import Wallet
from app.blockchain.bsc_client import get_slh_balance


def _mode_label(mode: str | None) -> str:
    mapping = {
        "noncustodial": "?? Non-Custodial (Self-Custody)",
        "custodial": "?? Custodial (Bank-Mode)",
        "hybrid": "?? Hybrid (Mix)",
    }
    return mapping.get(mode or "noncustodial", "?? Non-Custodial (Self-Custody)")


async def wallet(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.effective_user:
        return

    telegram_id = update.effective_user.id

    async with async_session_maker() as session:
        user = (
            await session.execute(
                select(UserModel).where(UserModel.telegram_id == telegram_id)
            )
        ).scalar_one_or_none()

        wallet = None
        if user:
            wallet = (
                await session.execute(
                    select(Wallet).where(Wallet.user_id == user.id)
                )
            ).scalar_one_or_none()

        if not user:
            user = UserModel(telegram_id=telegram_id)
            session.add(user)
            await session.flush()

        if not wallet:
            wallet = Wallet(user_id=user.id)
            session.add(wallet)
            await session.commit()
            await session.refresh(wallet)

    mode_text = _mode_label(getattr(user, "investment_mode", "noncustodial"))

    slh_onchain = get_slh_balance(wallet.bsc_address)
    slh_internal = wallet.balance_slh

    text = (
        "?? ???? GATE BOTSHOP ???\n\n"
        f"??? ???? ?????: {mode_text}\n\n"
        "?? ????? ?????????\n"
        f"• ???????? (USD): {wallet.balance_sim:.2f}\n"
        f"• ???? ????? (USD): {wallet.balance_real:.2f}\n"
        f"• SLH ?????: {slh_internal:.4f}\n"
        f"• MNH (???? ?-SLH): {wallet.balance_mnh:.4f}\n"
        f"• MNH ????: {wallet.locked_mnh:.4f}\n"
        f"• ZUZ (??????): {wallet.balance_zuz:.2f}\n\n"
        "?? SLH ?? ????\n"
        f"• ????? BSC: {wallet.bsc_address or '(??? ??????)'}\n"
        f"• SLH on-chain: {slh_onchain:.4f}\n\n"
        "?? ?????? TON\n"
        f"• Mainnet: {wallet.ton_mainnet or '(??? ?????)'}\n"
        f"• Testnet: {wallet.ton_testnet or '(??? ?????)'}\n\n"
        "?????:\n"
        "• ???? SLH ? MNH\n"
        "• ????? ?????? ???????\n"
        "• ?????? ?????? ?-ZUZ\n"
    )

    await update.effective_message.reply_text(text)

