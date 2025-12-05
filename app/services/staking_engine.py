from __future__ import annotations

from datetime import datetime, timedelta
from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..models.staking import StakePosition
from ..models.wallet import Wallet


async def create_stake(
    session: AsyncSession,
    wallet: Wallet,
    amount_slh: float,
    lock_days: int,
) -> StakePosition:
    apy = settings.STAKING_PLANS.get(lock_days)
    if apy is None:
        raise ValueError("Unsupported lock period")

    if wallet.balance_slh < amount_slh:
        raise ValueError("Insufficient balance")

    wallet.balance_slh -= amount_slh

    now = datetime.utcnow()
    ends_at = now + timedelta(days=lock_days)

    stake = StakePosition(
        user_id=wallet.user_id,
        is_demo=wallet.is_demo,
        amount_slh=amount_slh,
        lock_days=lock_days,
        apy=apy,
        active=True,
        started_at=now,
        ends_at=ends_at,
        last_yield_calculated_at=now,
    )
    session.add(stake)
    await session.flush()
    return stake


async def list_user_stakes(
    session: AsyncSession,
    user_id: int,
    is_demo: bool | None = None,
) -> List[StakePosition]:
    q = select(StakePosition).where(StakePosition.user_id == user_id)
    if is_demo is not None:
        q = q.where(StakePosition.is_demo == is_demo)
    res = await session.execute(q)
    return list(res.scalars().all())


async def settle_yield_for_stake(
    session: AsyncSession,
    stake: StakePosition,
    wallet: Wallet,
    now: datetime | None = None,
) -> float:
    if not stake.active:
        return 0.0

    if now is None:
        now = datetime.utcnow()

    if stake.last_yield_calculated_at is None:
        stake.last_yield_calculated_at = stake.started_at

    delta_days = (now - stake.last_yield_calculated_at).total_seconds() / 86400.0
    if delta_days <= 0:
        return 0.0

    daily_rate = stake.apy / 100.0 / 365.0
    reward = stake.amount_slh * daily_rate * delta_days

    wallet.balance_slh += reward
    stake.last_yield_calculated_at = now

    if now >= stake.ends_at:
        stake.active = False
        wallet.balance_slh += stake.amount_slh  # principal back

    await session.flush()
    return reward
