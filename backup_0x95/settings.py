from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes
from sqlalchemy import select

from app.database import async_session_maker
from app.models.users import User


def _settings_keyboard() -> ReplyKeyboardMarkup:
    keyboard = [
        [
            KeyboardButton("🔒 Non-Custodial"),
            KeyboardButton("🏦 Custodial"),
            KeyboardButton("🟨 Hybrid"),
        ]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def _mode_from_text(text: str) -> str | None:
    mapping = {
        "🔒 Non-Custodial": "noncustodial",
        "🏦 Custodial": "custodial",
        "🟨 Hybrid": "hybrid",
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
        "noncustodial": "🔒 Non-Custodial",
        "custodial": "🏦 Custodial",
        "hybrid": "🟨 Hybrid",
    }.get(current_mode, "🔒 Non-Custodial")

    text = (
        "⚙️ הגדרות מסחר\n\n"
        f"מצב נוכחי: {mode_label}\n\n"
        "בחר מצב חדש בעזרת הכפתורים למטה."
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
        # טקסט שלא קשור למצבי המסחר  מתעלמים
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
        f"מצב המסחר שלך עודכן ל{choice}.",
        reply_markup=_settings_keyboard(),
    )
