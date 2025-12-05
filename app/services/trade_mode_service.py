from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..models.user import User
from ..models.user_settings import UserSettings


async def get_or_create_user(
    session: AsyncSession,
    telegram_id: int,
    username: str | None,
    first_name: str | None,
) -> User:
    stmt = select(User).where(User.telegram_id == telegram_id)
    res = await session.execute(stmt)
    user = res.scalar_one_or_none()
    if user is None:
        user = User(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
        )
        session.add(user)
        await session.flush()
    return user


async def get_or_create_settings(session: AsyncSession, user: User) -> UserSettings:
    stmt = select(UserSettings).where(UserSettings.user_id == user.id)
    res = await session.execute(stmt)
    s = res.scalar_one_or_none()
    if s is None:
        s = UserSettings(
            user_id=user.id,
            trade_mode=settings.DEFAULT_TRADE_MODE,
            network=settings.DEFAULT_NETWORK,
            base_currency=settings.DEFAULT_BASE_CURRENCY,
        )
        session.add(s)
        await session.flush()
    return s


async def update_trade_mode(session: AsyncSession, user: User, mode: str) -> UserSettings:
    s = await get_or_create_settings(session, user)
    s.trade_mode = mode
    await session.flush()
    return s
