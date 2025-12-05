from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..models.user import User
from ..models.user_settings import UserSettings


DEFAULT_TRADE_MODE = "sim"  # sim / real / hybrid
DEFAULT_NETWORK = "ton_testnet"
DEFAULT_BASE_CURRENCY = "TON"


async def get_or_create_user(
    session: AsyncSession,
    telegram_id: int,
    username: str | None,
    first_name: str | None,
) -> User:
    stmt = select(User).where(User.telegram_id == telegram_id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()

    if user:
        # עדכון שם משתמש / שם פרטי אם השתנו
        changed = False
        if username and user.username != username:
            user.username = username
            changed = True
        if first_name and user.first_name != first_name:
            user.first_name = first_name
            changed = True
        if changed:
            session.add(user)
        return user

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
    result = await session.execute(stmt)
    settings_row = result.scalar_one_or_none()

    if settings_row:
        return settings_row

    settings_row = UserSettings(
        user_id=user.id,
        trade_mode=DEFAULT_TRADE_MODE,
        network=DEFAULT_NETWORK,
        base_currency=DEFAULT_BASE_CURRENCY,
    )
    session.add(settings_row)
    await session.flush()
    return settings_row


async def set_trade_mode(
    session: AsyncSession,
    user: User,
    mode: str,
) -> UserSettings:
    if mode not in ("sim", "real", "hybrid"):
        raise ValueError(f"Unknown trade mode: {mode}")

    settings_row = await get_or_create_settings(session, user)
    settings_row.trade_mode = mode
    session.add(settings_row)
    await session.flush()
    return settings_row
