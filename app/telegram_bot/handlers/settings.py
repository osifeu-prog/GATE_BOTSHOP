from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, Application

from ...database import AsyncSessionLocal
from ...services.trade_mode_service import (
    get_or_create_user,
    get_or_create_settings,
)
from ..keyboards import trade_mode_keyboard


async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user is None:
        return

    async with AsyncSessionLocal() as session:
        user = await get_or_create_user(
            session,
            telegram_id=update.effective_user.id,
            username=update.effective_user.username,
            first_name=update.effective_user.first_name,
        )
        settings_row = await get_or_create_settings(session, user)

    current = settings_row.trade_mode
    text = (
        "⚙️ הגדרות מסחר\n\n"
        f"המצב הנוכחי שלך: {current}\n\n"
        "באפשרותך לשנות את מצב המסחר בכל רגע:"
    )
    await update.effective_message.reply_text(
        text,
        reply_markup=trade_mode_keyboard(current=current),
    )


def register_settings_handlers(app: Application) -> None:
    app.add_handler(CommandHandler("settings", settings_command))
