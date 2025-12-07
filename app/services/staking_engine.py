from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.staking import StakingPosition

# תשואה שנתית ברירת מחדל (APY) – אפשר לשנות בהמשך / להעביר ל-ENV
DEFAULT_APY_PERCENT = Decimal("12")  # 12% לשנה


async def create_admin_stake(
    session: AsyncSession,
    telegram_user_id: int,
    principal_slh: Decimal,
    duration_days: int,
    apy_percent: Decimal | None = None,
) -> StakingPosition:
    """
    יצירת חיסכון חדש למשתמש ע"י אדמין.
    אין כאן עדיין חיבור on-chain – רק לוגיקת בנק פנימי.
    """

    if apy_percent is None:
        apy_percent = DEFAULT_APY_PERCENT

    opened_at = datetime.utcnow()
    closes_at = opened_at + timedelta(days=duration_days)

    # תשואה לינארית פשוטה לפי APY
    reward = (
        principal_slh
        * apy_percent
        * Decimal(duration_days)
        / Decimal(36500)  # /100 בשביל אחוז ו-365 ימים
    ).quantize(Decimal("0.0001"))

    position = StakingPosition(
        telegram_user_id=telegram_user_id,
        principal_slh=principal_slh,
        expected_reward_slh=reward,
        duration_days=duration_days,
        status="open",
        opened_at=opened_at,
        closes_at=closes_at,
    )
    session.add(position)
    await session.flush()  # כדי לקבל id
    return position


async def get_user_stakes(
    session: AsyncSession,
    telegram_user_id: int,
) -> Sequence[StakingPosition]:
    """
    כל החיסכונות של משתמש (פתוחים וסגורים) מהחדש לישן.
    """
    stmt = (
        select(StakingPosition)
        .where(StakingPosition.telegram_user_id == telegram_user_id)
        .order_by(StakingPosition.opened_at.desc())
    )
    result = await session.execute(stmt)
    return result.scalars().all()
