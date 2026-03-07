from telegram import Update
from telegram.ext import ContextTypes
from app.services.trading_ai_service import market_recommendation

async def ai_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sentiment = await market_recommendation()

    await update.message.reply_text(
        f"أ—آ ط¢ع؛أ¢â€ڑع¾أ¢â‚¬â€œ أ—آ³ط¢آ أ—آ³أ¢â€‍آ¢أ—آ³ط£â€”أ—آ³أ¢â‚¬آ¢أ—آ³أ¢â‚¬â€‌ AI:\n\nأ—آ³ط¢آ©أ—آ³أ¢â‚¬آ¢أ—آ³ط¢آ§ أ—آ³ط¢آ أ—آ³ط¢آ¨أ—آ³ط¢ع¯أ—آ³أ¢â‚¬â€Œ: {sentiment}"
    )




