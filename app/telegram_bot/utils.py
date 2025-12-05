from __future__ import annotations

from typing import Optional

from telegram import Update
from telegram.ext import ContextTypes


def get_user_identity(update: Update) -> tuple[int, Optional[str], Optional[str], Optional[str]]:
    tg_user = update.effective_user
    assert tg_user is not None
    return (
        tg_user.id,
        tg_user.username,
        tg_user.first_name,
        tg_user.last_name,
    )


async def reply_markdown(update: Update, text: str, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message:
        await update.message.reply_text(text, parse_mode="Markdown")
    elif update.callback_query:
        await update.callback_query.edit_message_text(text, parse_mode="Markdown")
