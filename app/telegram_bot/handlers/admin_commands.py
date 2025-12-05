from __future__ import annotations

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)

from ...config import settings
from ...database import AsyncSessionLocal
from ..admin_panel import admin_summary
from ..keyboards import admin_menu_kb


async def admin_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if settings.ADMIN_USER_ID is None or update.effective_user is None:
        return

    if update.effective_user.id != settings.ADMIN_USER_ID:
        await update.message.reply_text("אין לך הרשאה לאזור אדמין.")
        return

    async with AsyncSessionLocal() as session:
        summary = await admin_summary(session)

    await update.message.reply_text(summary, parse_mode="Markdown", reply_markup=admin_menu_kb())


def register_admin_handlers(app: Application) -> None:
    app.add_handler(CommandHandler("admin", admin_cmd))
