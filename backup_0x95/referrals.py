from telegram import Update
from telegram.ext import ContextTypes
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import async_session_maker
from app.services.referral_service import create_referral_link

async def referrals(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id

    async with async_session_maker() as session:
        code = await create_referral_link(session, uid)

    link = f"https://t.me/{context.bot.username}?start={code}"

    await update.message.reply_text(
        f"🎁 קישור ההפניה שלך:\n{link}"
    )
