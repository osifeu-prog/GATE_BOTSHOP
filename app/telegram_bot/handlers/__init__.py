from telegram.ext import Application, CommandHandler, MessageHandler, filters

from .start import start
from .wallet import wallet
from .settings import settings, set_mode
from .ai import ai_panel
from .staking import staking
from .referrals import referrals
from .admin import admin_panel, admin_tvl


def register_all_handlers(app: Application) -> None:
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("wallet", wallet))
    app.add_handler(CommandHandler("settings", settings))

    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(CommandHandler("admin_tvl", admin_tvl))

    app.add_handler(CommandHandler("ai", ai_panel))
    app.add_handler(CommandHandler("stake", staking))
    app.add_handler(CommandHandler("referrals", referrals))

    mode_filter = filters.TEXT & (~filters.COMMAND)
    app.add_handler(MessageHandler(mode_filter, set_mode))
