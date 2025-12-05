from __future__ import annotations

import secrets
from typing import Optional, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.user import User
from ..models.referrals import ReferralLink, ReferralRelation


def _generate_code() -> str:
    return secrets.token_urlsafe(8)


async def get_or_create_referral_link(
    session: AsyncSession,
    user: User,
) -> ReferralLink:
    q = select(ReferralLink).where(ReferralLink.user_id == user.id)
    res = await session.execute(q)
    link = res.scalar_one_or_none()
    if link is None:
        code = _generate_code()
        link = ReferralLink(user_id=user.id, code=code)
        session.add(link)
        await session.flush()
    return link


async def attach_referral(
    session: AsyncSession,
    parent: User,
    child: User,
) -> None:
    # prevent loops
    if parent.id == child.id:
        return

    q = select(ReferralRelation).where(
        ReferralRelation.parent_id == parent.id,
        ReferralRelation.child_id == child.id,
    )
    res = await session.execute(q)
    if res.scalar_one_or_none() is not None:
        return

    rel = ReferralRelation(parent_id=parent.id, child_id=child.id, level=1)
    session.add(rel)
    await session.flush()

    # simple propagation: parent-of-parent becomes level2, etc.
    qp = select(ReferralRelation).where(
        ReferralRelation.child_id == parent.id,
        ReferralRelation.level == 1,
    )
    res_p = await session.execute(qp)
    parent_rel = res_p.scalar_one_or_none()
    if parent_rel:
        rel2 = ReferralRelation(
            parent_id=parent_rel.parent_id,
            child_id=child.id,
            level=2,
        )
        session.add(rel2)
        await session.flush()
