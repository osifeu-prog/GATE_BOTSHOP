أ—ع؛ط¢آ»ط¢طںfrom telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes
from sqlalchemy import select

from app.database import async_session_maker
from app.models.users import User


def _settings_keyboard() -> ReplyKeyboardMarkup:
    keyboard = [
        [
            KeyboardButton("أ—آ ط¢ع؛أ¢â‚¬â€Œأ¢â‚¬â„¢ Non-Custodial"),
            KeyboardButton("أ—آ ط¢ع؛ط¢عˆط¢آ¦ Custodial"),
            KeyboardButton("أ—آ ط¢ع؛ط¢ع؛ط¢آ¨ Hybrid"),
        ]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def _mode_from_text(text: str) -> str | None:
    mapping = {
        "أ—آ ط¢ع؛أ¢â‚¬â€Œأ¢â‚¬â„¢ Non-Custodial": "noncustodial",
        "أ—آ ط¢ع؛ط¢عˆط¢آ¦ Custodial": "custodial",
        "أ—آ ط¢ع؛ط¢ع؛ط¢آ¨ Hybrid": "hybrid",
    }
    return mapping.get(text.strip())


async def settings(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.effective_user:
        return

    telegram_id = update.effective_user.id

    async with async_session_maker() as session:
        user = (
            await session.execute(
                select(User).where(User.telegram_id == telegram_id)
            )
        ).scalar_one_or_none()

    current_mode = user.investment_mode if user else "noncustodial"

    mode_label = {
        "noncustodial": "أ—آ ط¢ع؛أ¢â‚¬â€Œأ¢â‚¬â„¢ Non-Custodial",
        "custodial": "أ—آ ط¢ع؛ط¢عˆط¢آ¦ Custodial",
        "hybrid": "أ—آ ط¢ع؛ط¢ع؛ط¢آ¨ Hybrid",
    }.get(current_mode, "أ—آ ط¢ع؛أ¢â‚¬â€Œأ¢â‚¬â„¢ Non-Custodial")

    text = (
        "أ—â€™ط¢ع‘أ¢â€‍آ¢أ—ع؛ط¢آ¸ط¢عˆ أ—آ³أ¢â‚¬â€Œأ—آ³أ¢â‚¬â„¢أ—آ³أ¢â‚¬إ“أ—آ³ط¢آ¨أ—آ³أ¢â‚¬آ¢أ—آ³ط£â€” أ—آ³ط¢â€چأ—آ³ط¢طŒأ—آ³أ¢â‚¬â€‌أ—آ³ط¢آ¨\n\n"
        f"أ—آ³ط¢â€چأ—آ³ط¢آ¦أ—آ³أ¢â‚¬ع© أ—آ³ط¢آ أ—آ³أ¢â‚¬آ¢أ—آ³أ¢â‚¬ط›أ—آ³أ¢â‚¬â€‌أ—آ³أ¢â€‍آ¢: {mode_label}\n\n"
        "أ—آ³أ¢â‚¬ع©أ—آ³أ¢â‚¬â€‌أ—آ³ط¢آ¨ أ—آ³ط¢â€چأ—آ³ط¢آ¦أ—آ³أ¢â‚¬ع© أ—آ³أ¢â‚¬â€‌أ—آ³أ¢â‚¬إ“أ—آ³ط¢آ© أ—آ³أ¢â‚¬ع©أ—آ³ط¢آ¢أ—آ³أ¢â‚¬â€œأ—آ³ط¢آ¨أ—آ³ط£â€” أ—آ³أ¢â‚¬â€Œأ—آ³أ¢â‚¬ط›أ—آ³أ¢â€ڑع¾أ—آ³ط£â€”أ—آ³أ¢â‚¬آ¢أ—آ³ط¢آ¨أ—آ³أ¢â€‍آ¢أ—آ³ط¢â€Œ أ—آ³ط¢إ“أ—آ³ط¢â€چأ—آ³ط«إ“أ—آ³أ¢â‚¬â€Œ."
    )

    await update.effective_message.reply_text(
        text, reply_markup=_settings_keyboard()
    )


async def set_mode(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.effective_user or not update.effective_message:
        return

    choice = update.effective_message.text or ""
    new_mode = _mode_from_text(choice)
    if new_mode is None:
        # أ—آ³ط«إ“أ—آ³ط¢آ§أ—آ³ط¢طŒأ—آ³ط«إ“ أ—آ³ط¢آ©أ—آ³ط¢إ“أ—آ³ط¢ع¯ أ—آ³ط¢آ§أ—آ³ط¢آ©أ—آ³أ¢â‚¬آ¢أ—آ³ط¢آ¨ أ—آ³ط¢إ“أ—آ³ط¢â€چأ—آ³ط¢آ¦أ—آ³أ¢â‚¬ع©أ—آ³أ¢â€‍آ¢ أ—آ³أ¢â‚¬â€Œأ—آ³ط¢â€چأ—آ³ط¢طŒأ—آ³أ¢â‚¬â€‌أ—آ³ط¢آ¨  أ—آ³ط¢â€چأ—آ³ط£â€”أ—آ³ط¢آ¢أ—آ³ط¢إ“أ—آ³ط¢â€چأ—آ³أ¢â€‍آ¢أ—آ³ط¢â€Œ
        return

    telegram_id = update.effective_user.id

    async with async_session_maker() as session:
        user = (
            await session.execute(
                select(User).where(User.telegram_id == telegram_id)
            )
        ).scalar_one_or_none()

        if not user:
            user = User(telegram_id=telegram_id)
            session.add(user)

        user.investment_mode = new_mode
        await session.commit()

    await update.effective_message.reply_text(
        f"أ—آ³ط¢â€چأ—آ³ط¢آ¦أ—آ³أ¢â‚¬ع© أ—آ³أ¢â‚¬â€Œأ—آ³ط¢â€چأ—آ³ط¢طŒأ—آ³أ¢â‚¬â€‌أ—آ³ط¢آ¨ أ—آ³ط¢آ©أ—آ³ط¢إ“أ—آ³ط¢ع‘ أ—آ³ط¢آ¢أ—آ³أ¢â‚¬آ¢أ—آ³أ¢â‚¬إ“أ—آ³أ¢â‚¬ط›أ—آ³ط¢ع؛ أ—آ³ط¢إ“{choice}.",
        reply_markup=_settings_keyboard(),
    )



