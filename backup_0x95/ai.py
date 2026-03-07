from telegram import Update
from telegram.ext import ContextTypes
from app.services.trading_ai_service import market_recommendation

async def ai_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sentiment = await market_recommendation()

    await update.message.reply_text(
        f"🤖 ניתוח AI:\n\nשוק נראה: {sentiment}"
    )
