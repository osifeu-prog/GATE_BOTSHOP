from __future__ import annotations

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)

from ...database import AsyncSessionLocal
from ...config import settings
from ...services.wallet_engine import get_or_create_user, get_or_create_wallets
from ..keyboards import main_menu_kb, wallet_mode_kb
from ..utils import get_user_identity


async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    tid, username, first_name, last_name = get_user_identity(update)

    async with AsyncSessionLocal() as session:
        user = await get_or_create_user(session, tid, username, first_name, last_name)
        demo, real = await get_or_create_wallets(session, user)
        await session.commit()

    text = (
        "ברוך הבא ל־*GATE BOTSHOP AI* 🚀\n\n"
        "כאן תקבל:\n"
        "• התראות מסחר למטבעות מובילים\n"
        "• סטייקינג מדומה עם רווח יומי\n"
        "• דרגות, משימות ורפרלים\n\n"
        "בחר מצב עבודה לארנק שלך:"
    )
    await update.message.reply_text(
        text,
        parse_mode="Markdown",
        reply_markup=wallet_mode_kb(),
    )

    await update.message.reply_text(
        "תפריט ראשי:",
        reply_markup=main_menu_kb(),
    )


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        "פקודות זמינות:\n"
        "/start – תפריט פתיחה מחדש\n"
        "/wallet – סטטוס ארנק\n"
        "/stake – תפריט סטייקינג\n"
        "/mystakes – רשימת הסטייקינג שלך\n"
        "/rewards – מצב דרגות ו-XP\n"
        "/admin – תפריט אדמין (למנהל בלבד)"
    )
    await update.message.reply_text(text)


async def wallet_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    tid, username, first_name, last_name = get_user_identity(update)

    async with AsyncSessionLocal() as session:
        user = await get_or_create_user(session, tid, username, first_name, last_name)
        demo, real = await get_or_create_wallets(session, user)
        await session.commit()

    text = (
        "📊 *סטטוס ארנק*\n"
        f"מצב נוכחי: *{user.mode.upper()}*\n\n"
        f"*דמו:* {demo.balance_slh:.4f} SLH\n"
        f"*אמיתי:* {real.balance_slh:.4f} SLH"
    )
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=wallet_mode_kb())


def register_user_handlers(app: Application) -> None:
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("wallet", wallet_cmd))
