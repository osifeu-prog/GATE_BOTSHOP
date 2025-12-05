from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..models.user import User
from ..models.rewards import RewardEvent


async def add_reward(
    session: AsyncSession,
    user: User,
    kind: str,
    xp: int = 0,
    slh: float = 0.0,
) -> RewardEvent:
    user.xp += xp
    new_level = user.level
    for lvl_name, required_xp in sorted(
        settings.LEVELS.items(), key=lambda t: t[1]
    ):
        if user.xp >= required_xp:
            new_level = lvl_name
    user.level = new_level

    evt = RewardEvent(
        user_id=user.id,
        kind=kind,
        amount_xp=xp,
        amount_slh=slh,
    )
    session.add(evt)
    await session.flush()
    return evt
