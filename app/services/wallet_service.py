from __future__ import annotations

from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..models.wallet import Wallet


async def get_or_create_default_wallets(session: AsyncSession, user_id: int) -> List[Wallet]:
    """
    דואג שלמשתמש יהיו לפחות שני ארנקים:
    - REAL ברשת ברירת מחדל
    - DEMO ברשת ברירת מחדל
    """
    stmt = select(Wallet).where(Wallet.user_id == user_id)
    result = await session.execute(stmt)
    wallets = list(result.scalars().all())

    if wallets:
        return wallets

    default_net = settings.DEFAULT_NETWORK

    real_wallet = Wallet(
        user_id=user_id,
        network=default_net,
        kind="real",
        is_primary=True,
    )
    demo_wallet = Wallet(
        user_id=user_id,
        network=default_net,
        kind="demo",
        is_primary=False,
    )
    session.add(real_wallet)
    session.add(demo_wallet)
    await session.flush()

    return [real_wallet, demo_wallet]


async def get_wallets_for_user(session: AsyncSession, user_id: int) -> List[Wallet]:
    stmt = select(Wallet).where(Wallet.user_id == user_id)
    result = await session.execute(stmt)
    return list(result.scalars().all())
