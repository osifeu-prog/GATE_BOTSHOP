import logging

from telegram.ext import Application

from app.config import settings
from app.telegram_bot.handlers import register_all_handlers

logger = logging.getLogger("gate_botshop_ai")


def build_telegram_application() -> Application:
    app = (
        Application.builder()
        .token(settings.BOT_TOKEN)
        .concurrent_updates(True)
        .build()
    )

    register_all_handlers(app)
    logger.info("Telegram handlers registered.")
    return app
