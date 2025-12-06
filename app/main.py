from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse

from telegram import Update
from telegram.ext import Application

from .config import settings
from .database import init_db
from .telegram_bot.bot_app import build_telegram_app

# לוגger מרכזי
logger = logging.getLogger("gate_botshop_ai")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

# === FastAPI app ===
app = FastAPI(
    title="GATE BOTSHOP AI",
    version="0.2.0",
)

# נאחסן כאן את האפליקציה של טלגרם
telegram_app: Application | None = None


# --------------------------------------------------
#  Healthcheck + דף ראשי
# --------------------------------------------------
@app.get("/health")
async def health() -> Dict[str, Any]:
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/", response_class=HTMLResponse)
async def root(request: Request) -> HTMLResponse:
    # דף פשוט – כמו שאתה כבר רואה ברלווי
    html = """
    <!DOCTYPE html>
    <html lang="he">
    <head>
        <meta charset="UTF-8" />
        <title>GATE BOTSHOP – Dashboard</title>
        <style>
            body {
                font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
                background: radial-gradient(circle at top, #0f172a, #020617);
                color: #e5e7eb;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                min-height: 100vh;
                margin: 0;
            }
            .card {
                background: rgba(15, 23, 42, 0.9);
                border-radius: 16px;
                padding: 24px 28px;
                box-shadow: 0 20px 45px rgba(0, 0, 0, 0.5);
                max-width: 420px;
                text-align: center;
                border: 1px solid rgba(148, 163, 184, 0.2);
            }
            h1 {
                margin-top: 0;
                margin-bottom: 8px;
                font-size: 1.5rem;
            }
            p {
                margin: 4px 0;
            }
            .badge {
                display: inline-flex;
                align-items: center;
                gap: 6px;
                padding: 4px 10px;
                border-radius: 999px;
                background: rgba(34, 197, 94, 0.09);
                color: #4ade80;
                font-size: 0.75rem;
                margin-bottom: 12px;
            }
            .dot {
                width: 8px;
                height: 8px;
                border-radius: 999px;
                background: #22c55e;
                box-shadow: 0 0 12px rgba(34, 197, 94, 0.9);
            }
            .small {
                font-size: 0.8rem;
                color: #9ca3af;
                margin-top: 12px;
            }
        </style>
    </head>
    <body>
        <div class="card">
            <div class="badge">
                <div class="dot"></div>
                שרת פעיל
            </div>
            <h1>GATE BOTSHOP – Dashboard</h1>
            <p>שרת פעיל. כאן בעתיד יוצגו גרפים, סטטיסטיקות ונתוני מסחר.</p>
            <p class="small">Webhooks של טלגרם מנוהלים מהשרת הזה.</p>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html)


# --------------------------------------------------
#  Startup / Shutdown – DB + Telegram Application
# --------------------------------------------------
@app.on_event("startup")
async def on_startup() -> None:
    global telegram_app

    logger.info("Initializing DB connectivity...")
    await init_db()

    logger.info("Building Telegram Application...")
    # הבילדר של הבוט – מוגדר בקובץ bot_app.py שלך
    telegram_app = build_telegram_app(settings=settings)

    # חשוב מאוד: לאתחל ולהפעיל את האפליקציה לפני עיבוד עדכונים
    await telegram_app.initialize()
    await telegram_app.start()

    # בניית כתובת webhook מתוקנת
    base_url = str(settings.WEBHOOK_URL).rstrip("/")
    webhook_path = settings.TELEGRAM_WEBHOOK_PATH
    full_webhook_url = f"{base_url}{webhook_path}"

    await telegram_app.bot.set_webhook(
        url=full_webhook_url,
        allowed_updates=Update.ALL_TYPES,
    )
    logger.info("Telegram webhook set to %s", full_webhook_url)

    logger.info("Startup completed successfully.")


@app.on_event("shutdown")
async def on_shutdown() -> None:
    global telegram_app

    if telegram_app is not None:
        logger.info("Shutting down Telegram Application...")
        await telegram_app.stop()
        await telegram_app.shutdown()
        logger.info("Telegram Application stopped.")


# --------------------------------------------------
#  Webhook של טלגרם
# --------------------------------------------------
@app.post(settings.TELEGRAM_WEBHOOK_PATH)
async def telegram_webhook(update: dict) -> JSONResponse:
    """
    FastAPI endpoint שמקבל עדכונים מטלגרם,
    ומעביר אותם ל־python-telegram-bot Application.
    """
    global telegram_app

    if telegram_app is None:
        # אם משום מה ה־startup עוד לא סיים
        raise HTTPException(status_code=503, detail="Telegram application not ready")

    # המרנו את ה־dict ל־Update של טלגרם
    tg_update = Update.de_json(update, telegram_app.bot)

    await telegram_app.process_update(tg_update)
    return JSONResponse({"ok": True})
