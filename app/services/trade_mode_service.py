from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.user import User
from ..models.user_settings import UserSettings
from ..config import settings


async def get_or_create_user(session: AsyncSession, telegram_id: int, username: str | None, first_name: str | None) -> User:
    stmt = select(User).where(User.telegram_id == telegram_id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()
    if user:
        return user

    user = User(telegram_id=telegram_id, username=username, first_name=first_name)
    session.add(user)
    await session.flush()
    return user


async def get_or_create_settings(session: AsyncSession, user: User) -> UserSettings:
    stmt = select(UserSettings).where(UserSettings.user_id == user.id)
    result = await session.execute(stmt)
    row = result.scalar_one_or_none()
    if row:
        return row

    row = UserSettings(
        user_id=user.id,
        trade_mode=settings.DEFAULT_TRADE_MODE,
        network=settings.DEFAULT_NETWORK,
        base_currency=settings.DEFAULT_BASE_CURRENCY,
    )
    session.add(row)
    await session.flush()
    return row


async def set_trade_mode(session: AsyncSession, user: User, trade_mode: str) -> UserSettings:
    row = await get_or_create_settings(session, user)
    row.trade_mode = trade_mode
    await session.flush()
    return row
