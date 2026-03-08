from __future__ import annotations

import logging
from typing import Optional

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from telegram.ext import Application

from app.database import init_db
from app.telegram_bot.bot_app import build_telegram_application

app = FastAPI(title="BOTSHOP API")

telegram_app: Optional[Application] = None

@app.on_event("startup")
async def startup_event():
    global telegram_app
    await init_db()

    telegram_app = build_telegram_application()

    # במקום run_polling — הפעלה נכונה בתוך event loop של FastAPI
    await telegram_app.initialize()
    await telegram_app.start()
    await telegram_app.updater.start_polling()

@app.on_event("shutdown")
async def shutdown_event():
    global telegram_app
    if telegram_app:
        await telegram_app.updater.stop()
        await telegram_app.stop()
        await telegram_app.shutdown()

@app.get("/", response_class=HTMLResponse)
async def root():
    return "<h1>BOTSHOP is running</h1>"

@app.get("/health", response_class=JSONResponse)
async def health():
    return {"status": "ok"}
