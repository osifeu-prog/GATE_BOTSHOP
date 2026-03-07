أ—ع؛ط¢آ»ط¢طںfrom telegram import ReplyKeyboardMarkup
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.users import User
from app.models.staking_positions import StakingPosition
from app.services.trading_ai_service import market_recommendation

async def build_dynamic_keyboard(session: AsyncSession, user_id: int):
    user = await session.get(User, user_id)

    tier = user.user_tier if user else 1
    mode = user.investment_mode if user else "noncustodial"

    # AI STATUS (placeholder)
    ai_status = "أ—آ³أ¢â€ڑع¾أ—آ³ط¢آ¢أ—آ³أ¢â€‍آ¢أ—آ³ط¢إ“" if tier >= 2 else "أ—آ³أ¢â‚¬ط›أ—آ³أ¢â‚¬ع©أ—آ³أ¢â‚¬آ¢أ—آ³أ¢â€‍آ¢"

    # staking count
    stakes = (
        await session.execute(
            StakingPosition.__table__.select().where(StakingPosition.user_id == user_id)
        )
    ).fetchall()
    stake_count = len(stakes)

    header = f"أ—آ ط¢ع؛ط¢عˆط¢آ¦ أ—آ³ط¢â€چأ—آ³ط¢آ¦أ—آ³أ¢â‚¬ع©: {mode} | أ—آ ط¢ع؛ط¢عکأ¢â‚¬â€œ Tier {tier} | أ—آ ط¢ع؛أ¢â€ڑع¾أ¢â‚¬â€œ AI: {ai_status} | أ—آ ط¢ع؛أ¢â‚¬إ“ط¢ظ¹ أ—آ³ط¢طŒأ—آ³ط«إ“أ—آ³أ¢â€‍آ¢أ—آ³أ¢â€‍آ¢أ—آ³ط¢آ§أ—آ³أ¢â€‍آ¢أ—آ³ط¢â€Œ: {stake_count}"

    keyboard = [
        ["أ—آ ط¢ع؛أ¢â‚¬â„¢ط¢آ¼ أ—آ³ط¢ع¯أ—آ³ط¢آ¨أ—آ³ط¢آ أ—آ³ط¢آ§", "أ—آ ط¢ع؛أ¢â€ڑع¾أ¢â‚¬â€œ AI أ—آ³ط¢â€چأ—آ³ط¢طŒأ—آ³أ¢â‚¬â€‌أ—آ³ط¢آ¨"],
        ["أ—آ ط¢ع؛أ¢â‚¬إ“ط¢ظ¹ أ—آ³ط¢طŒأ—آ³ط«إ“أ—آ³أ¢â€‍آ¢أ—آ³أ¢â€‍آ¢أ—آ³ط¢آ§أ—آ³أ¢â€‍آ¢أ—آ³ط¢â€Œ", "أ—آ ط¢ع؛ط¢عکط¢ظ¾ أ—آ³أ¢â‚¬â€Œأ—آ³أ¢â€ڑع¾أ—آ³ط¢آ أ—آ³أ¢â€‍آ¢أ—آ³أ¢â‚¬آ¢أ—آ³ط£â€”"],
        ["أ—آ ط¢ع؛أ¢â‚¬â„¢ط¢آ± P2P", "أ—â€™ط¢ع‘أ¢â€‍آ¢ أ—آ³أ¢â‚¬â€Œأ—آ³أ¢â‚¬â„¢أ—آ³أ¢â‚¬إ“أ—آ³ط¢آ¨أ—آ³أ¢â‚¬آ¢أ—آ³ط£â€”"]
    ]

    return header, ReplyKeyboardMarkup(keyboard, resize_keyboard=True)



