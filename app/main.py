from __future__ import annotations

from datetime import datetime

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates

from telegram import Update
from telegram.ext import Application

from .config import settings
from .database import init_db
from .schemas import HealthResponse
from .telegram_bot.bot_app import build_telegram_app


app = FastAPI(title="GATE BOTSHOP AI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

templates = Jinja2Templates(directory="app/web")

telegram_app: Application | None = None


@app.on_event("startup")
async def on_startup() -> None:
    global telegram_app
    await init_db()

    telegram_app = build_telegram_app()
    await telegram_app.initialize()
    await telegram_app.start()

    base_url = str(settings.WEBHOOK_URL).rstrip("/")
    webhook_url = base_url + settings.TELEGRAM_WEBHOOK_PATH
    await telegram_app.bot.set_webhook(webhook_url)


@app.on_event("shutdown")
async def on_shutdown() -> None:
    global telegram_app
    if telegram_app is not None:
        await telegram_app.stop()
        await telegram_app.shutdown()
        telegram_app = None


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="ok", timestamp=datetime.utcnow())


@app.get("/", response_class=HTMLResponse)
async def root(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("dashboard.html", {"request": request})


@app.post(settings.TELEGRAM_WEBHOOK_PATH)
async def telegram_webhook(request: Request):
    global telegram_app
    if telegram_app is None:
        return JSONResponse({"ok": False, "error": "telegram_app not ready"}, status_code=503)

    data = await request.json()
    update = Update.de_json(data, telegram_app.bot)
    await telegram_app.process_update(update)
    return JSONResponse({"ok": True})
