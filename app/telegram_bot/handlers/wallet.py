from telegram import Update
from telegram.ext import ContextTypes
from sqlalchemy import select

from app.database import async_session_maker
from app.models.users import User as UserModel
from app.models.wallets import Wallet
from app.blockchain.bsc_client import get_slh_balance


def _mode_label(mode: str | None) -> str:
    mapping = {
        "noncustodial": "ظ‹ع؛ع؛آ© Nonأ¢â‚¬â€کCustodial (Selfأ¢â‚¬â€کCustody)",
        "custodial": "ظ‹ع؛عˆآ¦ Custodial (Bankأ¢â‚¬â€کMode)",
        "hybrid": "ظ‹ع؛ع؛آ¨ Hybrid (Mix)",
    }
    return mapping.get(mode or "noncustodial", "ظ‹ع؛ع؛آ© Nonأ¢â‚¬â€کCustodial (Selfأ¢â‚¬â€کCustody)")


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
        "ظ‹ع؛â€œظ¹ أ—ع¯أ—آ¨أ—آ أ—آ§ GATE BOTSHOP أ—آ©أ—إ“أ—ع‘\n\n"
        f"أ—â€چأ—آ¦أ—â€ک أ—â€چأ—طŒأ—â€”أ—آ¨ أ—آ أ—â€¢أ—â€؛أ—â€”أ—â„¢: {mode_text}\n\n"
        "ظ‹ع؛â€™آ° أ—â„¢أ—ع¾أ—آ¨أ—â€¢أ—ع¾ أ—آ¤أ—آ أ—â„¢أ—â€Œأ¢â‚¬â€کأ—â€چأ—آ¢أ—آ¨أ—â€؛أ—ع¾\n"
        f"أ¢â‚¬آ¢ أ—طŒأ—â„¢أ—â€چأ—â€¢أ—إ“أ—آ¦أ—â„¢أ—â€‌ (USD): {wallet.balance_sim:.2f}\n"
        f"أ¢â‚¬آ¢ أ—â€چأ—طŒأ—â€”أ—آ¨ أ—ع¯أ—â€چأ—â„¢أ—ع¾أ—â„¢ (USD): {wallet.balance_real:.2f}\n"
        f"أ¢â‚¬آ¢ SLH أ—آ¤أ—آ أ—â„¢أ—â€چأ—â„¢: {slh_internal:.4f}\n"
        f"أ¢â‚¬آ¢ MNH (أ—â€چأ—â€¢أ—â€چأ—آ¨ أ—â€چأ¢â‚¬â€کSLH): {wallet.balance_mnh:.4f}\n"
        f"أ¢â‚¬آ¢ MNH أ—آ أ—آ¢أ—â€¢أ—إ“: {wallet.locked_mnh:.4f}\n"
        f"أ¢â‚¬آ¢ ZUZ (أ—آ أ—آ§أ—â€¢أ—â€œأ—â€¢أ—ع¾): {wallet.balance_zuz:.2f}\n\n"
        "ظ‹ع؛â€‌â€” SLH أ—آ¢أ—إ“ أ—â€‌أ—آ¨أ—آ©أ—ع¾\n"
        f"أ¢â‚¬آ¢ أ—â€؛أ—ع¾أ—â€¢أ—â€کأ—ع¾ BSC: {wallet.bsc_address or '(أ—ع©أ—آ¨أ—â€Œ أ—â€‌أ—â€¢أ—â€™أ—â€œأ—آ¨أ—â€‌)'}\n"
        f"أ¢â‚¬آ¢ SLH onأ¢â‚¬â€کchain: {slh_onchain:.4f}\n\n"
        "ظ‹ع؛â€‌â€” أ—â€؛أ—ع¾أ—â€¢أ—â€کأ—â€¢أ—ع¾ TON\n"
        f"أ¢â‚¬آ¢ Mainnet: {wallet.ton_mainnet or '(أ—ع©أ—آ¨أ—â€Œ أ—â€‌أ—â€¢أ—â€™أ—â€œأ—آ¨)'}\n"
        f"أ¢â‚¬آ¢ Testnet: {wallet.ton_testnet or '(أ—ع©أ—آ¨أ—â€Œ أ—â€‌أ—â€¢أ—â€™أ—â€œأ—آ¨)'}\n\n"
        "أ—â€کأ—آ§أ—آ¨أ—â€¢أ—â€ک:\n"
        "أ¢â‚¬آ¢ أ—â€‌أ—â€چأ—آ¨أ—ع¾ SLH أ¢â€ â€™ MNH\n"
        "أ¢â‚¬آ¢ أ—â€چأ—آ©أ—â€”أ—آ§أ—â„¢ أ—â€”أ—â„¢أ—طŒأ—â€؛أ—â€¢أ—ع؛ أ—إ“أ—â€چأ—آ©أ—آ¤أ—â€”أ—â€¢أ—ع¾\n"
        "أ¢â‚¬آ¢ أ—â€چأ—آ©أ—â„¢أ—â€چأ—â€¢أ—ع¾ أ—â€¢أ—آ¤أ—آ¨أ—طŒأ—â„¢أ—â€Œ أ—â€کأ¢â‚¬â€کZUZ\n"
    )

    await update.effective_message.reply_text(text)


