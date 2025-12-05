from __future__ import annotations

from typing import Any, Dict

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from telegram import Update
from telegram.ext import Application

from app.config import settings, logger
from app.telegram_bot.handlers import get_handlers


telegram_app: Application | None = None

app = FastAPI(
    title="GATE BOTSHOP – AI Trading Gateway",
    version="0.2.0",
    description=(
        "שרת FastAPI + Telegram Bot שמספק התראות מסחר, ניתוחים קצרים, "
        "הסברים מבוססי AI והשוואת מחירי פיוצ'רז למטבעות BTC/ETH/BNB/SOL/XRP/TON."
    ),
)


@app.on_event("startup")
async def on_startup() -> None:
    global telegram_app

    logger.info("Initializing Telegram Application...")
    telegram_app = Application.builder().token(settings.BOT_TOKEN).build()

    for handler in get_handlers():
        telegram_app.add_handler(handler)

    await telegram_app.initialize()
    await telegram_app.start()

    webhook_url = settings.WEBHOOK_URL.rstrip("/") + settings.TELEGRAM_WEBHOOK_PATH
    await telegram_app.bot.set_webhook(webhook_url)

    logger.info("Telegram Application ready with webhook %s", webhook_url)


@app.on_event("shutdown")
async def on_shutdown() -> None:
    global telegram_app
    if telegram_app is None:
        return

    logger.info("Shutting down Telegram Application...")
    await telegram_app.bot.delete_webhook(drop_pending_updates=False)
    await telegram_app.stop()
    await telegram_app.shutdown()
    logger.info("Telegram Application stopped.")


@app.get("/health", tags=["infra"])
async def health() -> Dict[str, Any]:
    return {
        "status": "ok",
        "webhook_path": settings.TELEGRAM_WEBHOOK_PATH,
        "ai_provider": settings.AI_PROVIDER,
    }


@app.post(settings.TELEGRAM_WEBHOOK_PATH, tags=["telegram"])
async def telegram_webhook(update: Dict[str, Any]) -> JSONResponse:
    global telegram_app

    if telegram_app is None:
        raise HTTPException(status_code=503, detail="Telegram application not initialized")

    tg_update = Update.de_json(update, telegram_app.bot)
    await telegram_app.process_update(tg_update)
    return JSONResponse({"ok": True})
