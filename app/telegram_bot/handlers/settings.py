from __future__ import annotations

from telegram import Update
from telegram.ext import (
    ContextTypes,
    CommandHandler,
    CallbackQueryHandler,
    Application,
)

from ...database import AsyncSessionLocal
from ...services.trade_mode_service import (
    get_or_create_user,
    get_or_create_settings,
    update_trade_mode,
)
from ..keyboards import trade_mode_keyboard


async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user is None or update.effective_message is None:
        return

    async with AsyncSessionLocal() as session:
        user = await get_or_create_user(
            session,
            telegram_id=update.effective_user.id,
            username=update.effective_user.username,
            first_name=update.effective_user.first_name,
        )
        s = await get_or_create_settings(session, user)
        await session.commit()

    text = (
        "⚙️ הגדרות מסחר\n\n"
        f"המצב הנוכחי שלך: {s.trade_mode}\n\n"
        "באפשרותך לשנות את מצב המסחר בכל רגע:"
    )
    await update.effective_message.reply_text(text, reply_markup=trade_mode_keyboard())


async def trade_mode_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.callback_query is None or update.effective_user is None:
        return

    query = update.callback_query
    await query.answer()

    data = query.data or ""
    if not data.startswith("trade_mode:"):
        return

    mode = data.split(":", 1)[1]

    async with AsyncSessionLocal() as session:
        user = await get_or_create_user(
            session,
            telegram_id=update.effective_user.id,
            username=update.effective_user.username,
            first_name=update.effective_user.first_name,
        )
        s = await update_trade_mode(session, user, mode)
        await session.commit()

    msg = f"מצב המסחר שלך עודכן ל־{s.trade_mode}."
    await query.edit_message_text(msg)


def register_settings_handlers(app: Application) -> None:
    app.add_handler(CommandHandler("settings", settings_command))
    app.add_handler(CallbackQueryHandler(trade_mode_callback, pattern=r"^trade_mode:"))
