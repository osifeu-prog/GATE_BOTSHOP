from __future__ import annotations

from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, Application

from ...database import AsyncSessionLocal
from ...services.trade_mode_service import get_or_create_user, get_or_create_settings
from ..keyboards import trade_mode_keyboard


WELCOME_TEXT = (
    "ברוך הבא ל־GATE BOTSHOP AI 🚀\n\n"
    "כאן תקבל:\n"
    "• ניתוחי שוק חכמים\n"
    "• סימולציית מסחר בטוחה\n"
    "• בהמשך – מסחר אמיתי על TON/DEX, סטייקינג ו-P2P.\n\n"
    "בחר איך תרצה לסחור:"
)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user is None or update.effective_message is None:
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

    await update.effective_message.reply_text(
        WELCOME_TEXT,
        reply_markup=trade_mode_keyboard(),
    )


def register_start_handlers(app: Application) -> None:
    app.add_handler(CommandHandler("start", start_command))
