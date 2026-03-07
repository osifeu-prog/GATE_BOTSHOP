from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.users import User
from app.models.staking_positions import StakingPosition

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
    לוגיקה פנימית בלבד – נשמרת בטבלת staking_positions.
    """

    # למצוא את המשתמש לפי telegram_id
    user = (
        await session.execute(
            select(User).where(User.telegram_id == telegram_user_id)
        )
    ).scalar_one_or_none()

    if user is None:
        raise ValueError(f"User with telegram_id={telegram_user_id} not found")

    if apy_percent is None:
        apy_percent = DEFAULT_APY_PERCENT

    opened_at = datetime.utcnow()
    unlock_at = opened_at + timedelta(days=duration_days)

    # המודל הקיים עובד עם amount / days / apy
    pos = StakingPosition(
        user_id=user.id,
        amount=float(principal_slh),
        days=duration_days,
        apy=float(apy_percent),
        unlock_at=unlock_at,
        status="active",
    )

    session.add(pos)
    await session.commit()
    await session.refresh(pos)
    return pos


async def get_user_stakes(
    session: AsyncSession,
    telegram_user_id: int,
) -> Sequence[StakingPosition]:
    """
    כל החיסכונות של משתמש (פתוחים וסגורים) מהחדש לישן.
    """
    user = (
        await session.execute(
            select(User).where(User.telegram_id == telegram_user_id)
        )
    ).scalar_one_or_none()

    if user is None:
        return []

    stmt = (
        select(StakingPosition)
        .where(StakingPosition.user_id == user.id)
        .order_by(StakingPosition.created_at.desc())
    )
    result = await session.execute(stmt)
    return result.scalars().all()
