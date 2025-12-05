from telegram.ext import Application

from ..config import settings
from .handlers.start import register_start_handlers
from .handlers.settings import register_settings_handlers


def build_telegram_app() -> Application:
    app = (
        Application.builder()
        .token(settings.BOT_TOKEN)
        .concurrent_updates(True)
        .build()
    )

    register_start_handlers(app)
    register_settings_handlers(app)

    return app
