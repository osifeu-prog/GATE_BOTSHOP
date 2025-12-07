from telegram import Update
from telegram.ext import ContextTypes
from sqlalchemy import select

from app.database import async_session_maker
from app.models.users import User as UserModel
from app.models.wallets import Wallet


def _mode_label(mode: str | None) -> str:
    mapping = {
        "noncustodial": "🟩 Non-Custodial (Self-Custody)",
        "custodial": "🏦 Custodial (Bank-Mode)",
        "hybrid": "🟨 Hybrid (Mix)",
    }
    return mapping.get(mode or "noncustodial", "🟩 Non-Custodial (Self-Custody)")


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

    text = (
        "📊 ארנק GATE BOTSHOP שלך\n\n"
        f"מצב מסחר נוכחי: {mode_text}\n\n"
        "💰 יתרות פניםמערכת\n"
        f"• סימולציה (USD): {wallet.balance_sim:.2f}\n"
        f"• מסחר אמיתי (USD): {wallet.balance_real:.2f}\n"
        f"• SLH פנימי: {wallet.balance_slh:.4f}\n\n"
        "🔗 כתובות TON\n"
        f"• Mainnet: {wallet.ton_mainnet or '(טרם הוגדר)'}\n"
        f"• Testnet: {wallet.ton_testnet or '(טרם הוגדר)'}\n\n"
        "בהמשך נוסיף כאן גם:\n"
        "• סטייקינג אמיתי על TON/SLH\n"
        "• מצב P2P מלא\n"
        "• חיבור ישיר לבורסות (DEX/Hybrid).\n"
    )

    await update.effective_message.reply_text(text)
