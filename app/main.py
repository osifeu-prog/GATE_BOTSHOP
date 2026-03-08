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

app = FastAPI(title="BOTSHOP API")

telegram_app: Optional[Application] = None

@app.on_event("startup")
async def startup_event():
    global telegram_app
    await init_db()
    telegram_app = build_telegram_application()
    telegram_app.run_polling(stop_signals=None)

@app.get("/", response_class=HTMLResponse)
async def root():
    return "<h1>BOTSHOP is running</h1>"

@app.get("/health", response_class=JSONResponse)
async def health():
    return {"status": "ok"}
