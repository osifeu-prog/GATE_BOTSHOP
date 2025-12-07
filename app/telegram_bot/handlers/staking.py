from telegram import Update
from telegram.ext import ContextTypes
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import async_session_maker
from app.services.staking_service import create_stake

async def staking(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "כאן יופיעו ריביות, סטייקים ונתונים."
    )
