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
    # יאשר רק אם מצב ההשקעה מאפשר סטייקינג
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
