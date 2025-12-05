from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.user import User
from ..models.staking import StakePosition
from ..models.referrals import ReferralRelation


async def admin_summary(session: AsyncSession) -> str:
    users_count = (await session.execute(select(func.count(User.id)))).scalar() or 0
    stakes_count = (await session.execute(select(func.count(StakePosition.id)))).scalar() or 0
    referrals_count = (await session.execute(select(func.count(ReferralRelation.id)))).scalar() or 0

    return (
        "📊 *סטטוס מערכת*\n"
        f"- משתמשים רשומים: *{users_count}*\n"
        f"- עסקאות סטייקינג: *{stakes_count}*\n"
        f"- קשרי רפרל: *{referrals_count}*"
    )
