from __future__ import annotations

import logging
from typing import Any, Optional

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from telegram import Update
from telegram.ext import Application

from app.config import settings
from app.database import init_db
from app.telegram_bot.bot_app import build_telegram_application

logger = logging.getLogger("gate_botshop_ai")

app = FastAPI(title=settings.PROJECT_NAME)
telegram_app: Optional[Application] = None


@app.on_event("startup")
async def on_startup() -> None:
    global telegram_app

    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL, logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    logger.info("Starting GATE BOTSHOP backend...")
    await init_db()

    telegram_app = build_telegram_application()
    await telegram_app.initialize()

    await telegram_app.bot.set_webhook(
        url=f"{settings.WEBHOOK_URL}{settings.TELEGRAM_WEBHOOK_PATH}",
        allowed_updates=Update.ALL_UPDATES,
    )

    logger.info(
        "Telegram webhook set to %s%s",
        settings.WEBHOOK_URL,
        settings.TELEGRAM_WEBHOOK_PATH,
    )


@app.on_event("shutdown")
async def on_shutdown() -> None:
    global telegram_app
    if telegram_app is not None:
        await telegram_app.bot.delete_webhook()
        await telegram_app.shutdown()
        await telegram_app.stop()
        logger.info("Telegram application stopped.")


@app.get("/health")
async def health() -> dict[str, Any]:
    from datetime import datetime

    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}


@app.get("/")
async def root() -> HTMLResponse:
    return HTMLResponse(
        "<h1>GATE BOTSHOP  Dashboard</h1>"
        "<p>שרת פעיל. כאן בעתיד יוצגו גרפים, סטטיסטיקות ונתוני מסחר.</p>"
    )


@app.post(settings.TELEGRAM_WEBHOOK_PATH)
async def telegram_webhook(request: Request) -> JSONResponse:
    global telegram_app
    if telegram_app is None:
        logger.error("Telegram application is not initialized.")
        return JSONResponse(
            {"ok": False, "error": "bot not initialized"},
            status_code=500,
        )

    data = await request.json()
    update = Update.de_json(data=data, bot=telegram_app.bot)
    await telegram_app.process_update(update)
    return JSONResponse({"ok": True})
