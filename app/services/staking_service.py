from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.staking_positions import StakingPosition
from app.services.investment_manager import enforce_or_reject


async def create_stake(
    session: AsyncSession,
    user_id: int,
    amount: float,
    days: int,
    apy: float,
) -> StakingPosition:
    # أ—â„¢أ—ع¯أ—آ©أ—آ¨ أ—آ¨أ—آ§ أ—ع¯أ—â€Œ أ—â€چأ—آ¦أ—â€ک أ—â€‌أ—â€‌أ—آ©أ—آ§أ—آ¢أ—â€‌ أ—â€چأ—ع¯أ—آ¤أ—آ©أ—آ¨ أ—طŒأ—ع©أ—â„¢أ—â„¢أ—آ§أ—â„¢أ—آ أ—â€™
    await enforce_or_reject(session, user_id, "stake")

    unlock_time = datetime.utcnow() + timedelta(days=days)
    pos = StakingPosition(
        user_id=user_id,
        amount=amount,
        days=days,
        apy=apy,
        unlock_at=unlock_time,
    )
    session.add(pos)
    await session.commit()
    await session.refresh(pos)
    return pos



