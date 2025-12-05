from __future__ import annotations

from typing import Optional, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.user import User
from ..models.wallet import Wallet


async def get_or_create_user(
    session: AsyncSession,
    telegram_id: int,
    username: Optional[str],
    first_name: Optional[str],
    last_name: Optional[str],
) -> User:
    q = select(User).where(User.telegram_id == telegram_id)
    res = await session.execute(q)
    user = res.scalar_one_or_none()
    if user is None:
        user = User(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
        )
        session.add(user)
        await session.flush()
    return user


async def get_or_create_wallets(
    session: AsyncSession, user: User
) -> Tuple[Wallet, Wallet]:
    q = select(Wallet).where(Wallet.user_id == user.id)
    res = await session.execute(q)
    wallets = res.scalars().all()

    demo = None
    real = None
    for w in wallets:
        if w.is_demo:
            demo = w
        else:
            real = w

    if demo is None:
        demo = Wallet(user_id=user.id, is_demo=True, balance_slh=1000.0, balance_usdt=0.0)
        session.add(demo)

    if real is None:
        real = Wallet(user_id=user.id, is_demo=False, balance_slh=0.0, balance_usdt=0.0)
        session.add(real)

    await session.flush()
    return demo, real


async def adjust_balance(
    session: AsyncSession,
    wallet: Wallet,
    delta_slh: float = 0.0,
    delta_usdt: float = 0.0,
) -> Wallet:
    wallet.balance_slh += delta_slh
    wallet.balance_usdt += delta_usdt
    await session.flush()
    return wallet
