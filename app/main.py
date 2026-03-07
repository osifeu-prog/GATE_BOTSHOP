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

