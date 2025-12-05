from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler, Application

from ...database import AsyncSessionLocal
from ...services.trade_mode_service import (
    get_or_create_user,
    get_or_create_settings,
    set_trade_mode,
)
from ..keyboards import trade_mode_keyboard


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user is None:
        return

    async with AsyncSessionLocal() as session:
        user = await get_or_create_user(
            session,
            telegram_id=update.effective_user.id,
            username=update.effective_user.username,
            first_name=update.effective_user.first_name,
        )
        await get_or_create_settings(session, user)
        await session.commit()

    text = (
        "ברוך הבא ל־GATE BOTSHOP AI 🚀\n\n"
        "בחר איך תרצה לסחור:\n\n"
        "🟦 A. מסחר אמיתי (On-Chain / DEX)\n"
        "🟩 B. סימולציה (Futures SIM)\n"
        "🟨 C. מצב היברידי (Hybrid)"
    )
    await update.effective_message.reply_text(
        text,
        reply_markup=trade_mode_keyboard(),
    )


async def trade_mode_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user is None or update.callback_query is None:
        return

    query = update.callback_query
    await query.answer()

    data = query.data
    mode_map = {
        "mode_real": "real",
        "mode_sim": "sim",
        "mode_hybrid": "hybrid",
    }
    if data not in mode_map:
        return

    new_mode = mode_map[data]

    async with AsyncSessionLocal() as session:
        user = await get_or_create_user(
            session,
            telegram_id=update.effective_user.id,
            username=update.effective_user.username,
            first_name=update.effective_user.first_name,
        )
        await set_trade_mode(session, user, new_mode)
        await session.commit()

    msg = {
        "real": "מצב המסחר שלך עודכן ל־🟦 מסחר אמיתי (DEX).",
        "sim": "מצב המסחר שלך עודכן ל־🟩 סימולציה (Futures SIM).",
        "hybrid": "מצב המסחר שלך עודכן ל־🟨 מצב היברידי (Hybrid).",
    }[new_mode]

    await query.edit_message_text(msg)


def register_start_handlers(app: Application) -> None:
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CallbackQueryHandler(trade_mode_callback, pattern="^mode_"))
