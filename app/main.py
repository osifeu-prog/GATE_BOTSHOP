from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from telegram import Update
from telegram.ext import Application

from .config import settings
from .database import init_db
from .telegram_bot.bot_app import build_telegram_app

logger = logging.getLogger("gate_botshop_ai")
logging.basicConfig(level=getattr(logging, settings.LOG_LEVEL, logging.INFO))

app = FastAPI(title="Gate Botshop AI - Full Trading Stack")

app.mount("/static", StaticFiles(directory="app/web"), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

telegram_app: Application | None = None


@app.on_event("startup")
async def on_startup() -> None:
    global telegram_app
    logger.info("Initializing DB connectivity...")
    await init_db()

    logger.info("Building Telegram Application...")
    telegram_app = build_telegram_app()
    await telegram_app.initialize()
    await telegram_app.start()

    # כאן התיקון – המרה ל-string לפני rstrip
    base_url = str(settings.WEBHOOK_URL).rstrip("/")
    webhook_url = base_url + settings.TELEGRAM_WEBHOOK_PATH

    await telegram_app.bot.set_webhook(webhook_url)
    logger.info("Telegram webhook set to %s", webhook_url)


@app.on_event("shutdown")
async def on_shutdown() -> None:
    global telegram_app
    if telegram_app:
        await telegram_app.bot.delete_webhook()
        await telegram_app.stop()
        await telegram_app.shutdown()


@app.get("/health", response_class=JSONResponse)
async def health() -> dict[str, Any]:
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse)
async def root(request: Request) -> Any:
    html = '''
    <!DOCTYPE html>
    <html lang="he">
      <head>
        <meta charset="UTF-8" />
        <title>Gate Botshop AI</title>
      </head>
      <body>
        <h1>Gate Botshop AI – Online</h1>
        <p>הבוט פועל. רוב הפונקציונליות זמינה דרך טלגרם.</p>
      </body>
    </html>
    '''
    return HTMLResponse(content=html)


@app.post(settings.TELEGRAM_WEBHOOK_PATH)
async def telegram_webhook(request: Request) -> Response:
    global telegram_app
    if telegram_app is None:
        return Response(status_code=503)

    data = await request.json()
    update = Update.de_json(data, telegram_app.bot)
    await telegram_app.process_update(update)
    return Response(status_code=200)
