from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates

from telegram import Update
from telegram.ext import Application

from .config import settings
from .database import init_db
from .telegram_bot.handlers import (
    register_user_handlers,
    register_callback_handlers,
    register_admin_handlers,
)

logger = logging.getLogger("gate_botshop_ai")
logging.basicConfig(level=getattr(logging, settings.__dict__.get("LOG_LEVEL", "INFO"), logging.INFO))

app = FastAPI(title="Gate Botshop AI")

# Static + templates (basic)
app.mount("/static", StaticFiles(directory="app/web"), name="static")
templates = Jinja2Templates(directory="app/web")

# Allow CORS for future dashboards
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
    logger.info("Initializing DB...")
    await init_db()

    logger.info("Initializing Telegram Application...")
    telegram_app = (
        Application.builder()
        .token(settings.BOT_TOKEN)
        .concurrent_updates(True)
        .build()
    )

    register_user_handlers(telegram_app)
    register_callback_handlers(telegram_app)
    register_admin_handlers(telegram_app)

    await telegram_app.initialize()
    await telegram_app.start()

    webhook_url = settings.WEBHOOK_URL.rstrip("/") + settings.TELEGRAM_WEBHOOK_PATH
    await telegram_app.bot.set_webhook(webhook_url)
    logger.info("Telegram Application ready with webhook %s", webhook_url)


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
    return templates.TemplateResponse("dashboard.html", {"request": request})


@app.post(settings.TELEGRAM_WEBHOOK_PATH)
async def telegram_webhook(request: Request) -> Response:
    global telegram_app
    if telegram_app is None:
        return Response(status_code=503)

    data = await request.json()
    update = Update.de_json(data, telegram_app.bot)
    await telegram_app.process_update(update)
    return Response(status_code=200)
