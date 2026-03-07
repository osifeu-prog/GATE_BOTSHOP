from telegram import ReplyKeyboardMarkup
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.users import User
from app.models.staking_positions import StakingPosition
from app.services.trading_ai_service import market_recommendation

async def build_dynamic_keyboard(session: AsyncSession, user_id: int):
    user = await session.get(User, user_id)

    tier = user.user_tier if user else 1
    mode = user.investment_mode if user else "noncustodial"

    # AI STATUS (placeholder)
    ai_status = "פעיל" if tier >= 2 else "כבוי"

    # staking count
    stakes = (
        await session.execute(
            StakingPosition.__table__.select().where(StakingPosition.user_id == user_id)
        )
    ).fetchall()
    stake_count = len(stakes)

    header = f"🏦 מצב: {mode} | 🎖 Tier {tier} | 🤖 AI: {ai_status} | 📊 סטייקים: {stake_count}"

    keyboard = [
        ["💼 ארנק", "🤖 AI מסחר"],
        ["📊 סטייקים", "🎁 הפניות"],
        ["💱 P2P", "⚙ הגדרות"]
    ]

    return header, ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
