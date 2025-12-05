from __future__ import annotations

from telegram import Update


def get_chat_id(update: Update) -> int | None:
    if update.effective_chat:
        return update.effective_chat.id
    return None
