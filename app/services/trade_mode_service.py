from __future__ import annotations

import logging
from typing import Any, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.user import User
from ..models.user_settings import UserSettings

logger = logging.getLogger("gate_botshop_ai.trade_mode")


TRADE_MODES = ("sim", "hybrid", "real")


def normalize_trade_mode(value: str | None) -> str:
    if value in TRADE_MODES:
        return value
    return "sim"


def get_trade_mode_label(value: str | None) -> str:
    mode = normalize_trade_mode(value)
    if mode == "real":
        return "أ—آ ط¢ع؛ط¢ع؛ط¢آ¦ أ—آ³ط¢â€چأ—آ³ط¢طŒأ—آ³أ¢â‚¬â€‌أ—آ³ط¢آ¨ أ—آ³ط¢ع¯أ—آ³ط¢â€چأ—آ³أ¢â€‍آ¢أ—آ³ط£â€”أ—آ³أ¢â€‍آ¢ (On-Chain / DEX)"
    if mode == "hybrid":
        return "أ—آ ط¢ع؛ط¢ع؛ط¢آ¨ أ—آ³ط¢â€چأ—آ³ط¢آ¦أ—آ³أ¢â‚¬ع© أ—آ³أ¢â‚¬â€Œأ—آ³أ¢â€‍آ¢أ—آ³أ¢â‚¬ع©أ—آ³ط¢آ¨أ—آ³أ¢â€‍آ¢أ—آ³أ¢â‚¬إ“أ—آ³أ¢â€‍آ¢ (Hybrid: أ—آ³ط¢طŒأ—آ³أ¢â€‍آ¢أ—آ³ط¢â€چأ—آ³أ¢â‚¬آ¢أ—آ³ط¢إ“أ—آ³ط¢آ¦أ—آ³أ¢â€‍آ¢أ—آ³أ¢â‚¬â€Œ + أ—آ³ط¢â€چأ—آ³ط¢طŒأ—آ³أ¢â‚¬â€‌أ—آ³ط¢آ¨ أ—آ³ط¢ع¯أ—آ³ط¢â€چأ—آ³أ¢â€‍آ¢أ—آ³ط£â€”أ—آ³أ¢â€‍آ¢)"
    # sim
    return "أ—آ ط¢ع؛ط¢ع؛ط¢آ© أ—آ³ط¢طŒأ—آ³أ¢â€‍آ¢أ—آ³ط¢â€چأ—آ³أ¢â‚¬آ¢أ—آ³ط¢إ“أ—آ³ط¢آ¦أ—آ³أ¢â€‍آ¢أ—آ³أ¢â€‍آ¢أ—آ³ط£â€” أ—آ³ط¢â€چأ—آ³ط¢طŒأ—آ³أ¢â‚¬â€‌أ—آ³ط¢آ¨ (أ—آ³ط¢إ“أ—آ³ط¢إ“أ—آ³ط¢ع¯ أ—آ³ط¢طŒأ—آ³أ¢â€‍آ¢أ—آ³أ¢â‚¬ط›أ—آ³أ¢â‚¬آ¢أ—آ³ط¢ع؛ أ—آ³ط¢ع¯أ—آ³ط¢â€چأ—آ³أ¢â€‍آ¢أ—آ³ط£â€”أ—آ³أ¢â€‍آ¢)"


async def get_or_create_user(
    session: AsyncSession,
    tg_user: Any,
) -> User:
    """
    أ—آ³أ¢â‚¬إ“أ—آ³أ¢â‚¬آ¢أ—آ³ط¢ع¯أ—آ³أ¢â‚¬â„¢ أ—آ³ط¢آ©أ—آ³ط£â€”أ—آ³أ¢â‚¬â€Œأ—آ³أ¢â€‍آ¢أ—آ³أ¢â‚¬â€Œ أ—آ³ط¢آ¨أ—آ³ط¢آ©أ—آ³أ¢â‚¬آ¢أ—آ³ط¢â€چأ—آ³ط£â€” User أ—آ³ط¢إ“أ—آ³أ¢â‚¬ط›أ—آ³ط¢إ“ أ—آ³ط¢â€چأ—آ³ط¢آ©أ—آ³ط£â€”أ—آ³ط¢â€چأ—آ³ط¢آ© أ—آ³ط«إ“أ—آ³ط¢إ“أ—آ³أ¢â‚¬â„¢أ—آ³ط¢آ¨أ—آ³ط¢â€Œ.
    """
    stmt = select(User).where(User.telegram_id == tg_user.id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()

    if user is None:
        user = User(
            telegram_id=tg_user.id,
            username=tg_user.username,
            first_name=tg_user.first_name,
            last_name=tg_user.last_name,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        logger.info("Created new user %s (%s)", tg_user.id, tg_user.username)
    else:
        # أ—آ³ط¢آ¢أ—آ³أ¢â‚¬إ“أ—آ³أ¢â‚¬ط›أ—آ³أ¢â‚¬آ¢أ—آ³ط¢ع؛ أ—آ³ط¢آ§أ—آ³ط¢إ“ أ—آ³ط¢ع¯أ—آ³ط¢â€Œ أ—آ³أ¢â‚¬â€Œأ—آ³ط¢آ©أ—آ³ط¢â€Œ/أ—آ³أ¢â€‍آ¢أ—آ³أ¢â‚¬آ¢أ—آ³أ¢â‚¬â€œأ—آ³ط¢آ¨ أ—آ³أ¢â‚¬â€Œأ—آ³ط¢آ©أ—آ³ط£â€”أ—آ³ط¢آ أ—آ³أ¢â‚¬آ¢
        changed = False
        if user.username != tg_user.username:
            user.username = tg_user.username
            changed = True
        if user.first_name != tg_user.first_name:
            user.first_name = tg_user.first_name
            changed = True
        if user.last_name != tg_user.last_name:
            user.last_name = tg_user.last_name
            changed = True
        if changed:
            session.add(user)
            await session.commit()

    return user


async def get_or_create_settings(
    session: AsyncSession,
    user: User,
) -> UserSettings:
    """
    أ—آ³أ¢â‚¬â€Œأ—آ³أ¢â‚¬â„¢أ—آ³أ¢â‚¬إ“أ—آ³ط¢آ¨أ—آ³أ¢â‚¬آ¢أ—آ³ط£â€” أ—آ³أ¢â‚¬ع©أ—آ³ط¢آ¨أ—آ³أ¢â€‍آ¢أ—آ³ط¢آ¨أ—آ³ط£â€” أ—آ³ط¢â€چأ—آ³أ¢â‚¬â€‌أ—آ³أ¢â‚¬إ“أ—آ³ط¢إ“ أ—آ³ط¢إ“أ—آ³أ¢â‚¬ط›أ—آ³ط¢إ“ أ—آ³ط¢â€چأ—آ³ط¢آ©أ—آ³ط£â€”أ—آ³ط¢â€چأ—آ³ط¢آ© أ—â€™أ¢â€ڑآ¬أ¢â‚¬إ“ أ—آ³ط¢â€چأ—آ³ط¢آ¦أ—آ³أ¢â‚¬ع© أ—آ³ط¢â€چأ—آ³ط¢طŒأ—آ³أ¢â‚¬â€‌أ—آ³ط¢آ¨, أ—آ³ط¢â€چأ—آ³ط«إ“أ—آ³أ¢â‚¬ع©أ—آ³ط¢آ¢ أ—آ³أ¢â‚¬ع©أ—آ³ط¢طŒأ—آ³أ¢â€‍آ¢أ—آ³ط¢طŒ أ—آ³أ¢â‚¬آ¢أ—آ³أ¢â‚¬ط›أ—آ³أ¢â‚¬آ¢'.
    """
    stmt = select(UserSettings).where(UserSettings.user_id == user.id)
    result = await session.execute(stmt)
    settings = result.scalar_one_or_none()

    if settings is None:
        settings = UserSettings(
            user_id=user.id,
            trade_mode="sim",
            base_currency="USD",
            risk_profile="normal",
        )
        session.add(settings)
        await session.commit()
        await session.refresh(settings)
        logger.info("Created default settings for user_id=%s", user.id)

    # أ—آ³أ¢â‚¬آ¢أ—آ³أ¢â‚¬إ“أ—آ³ط¢ع¯ أ—آ³ط¢آ©أ—آ³ط¢â€چأ—آ³ط¢آ¦أ—آ³أ¢â‚¬ع© أ—آ³أ¢â‚¬â€Œأ—آ³ط¢â€چأ—آ³ط¢طŒأ—آ³أ¢â‚¬â€‌أ—آ³ط¢آ¨ أ—آ³أ¢â‚¬â€‌أ—آ³أ¢â‚¬آ¢أ—آ³ط¢آ§أ—آ³أ¢â€‍آ¢
    settings.trade_mode = normalize_trade_mode(settings.trade_mode)
    return settings


async def update_trade_mode(
    session: AsyncSession,
    user: User,
    new_mode: str,
) -> UserSettings:
    """
    أ—آ³ط¢آ¢أ—آ³أ¢â‚¬إ“أ—آ³أ¢â‚¬ط›أ—آ³أ¢â‚¬آ¢أ—آ³ط¢ع؛ أ—آ³ط¢â€چأ—آ³ط¢آ¦أ—آ³أ¢â‚¬ع© أ—آ³أ¢â‚¬â€Œأ—آ³ط¢â€چأ—آ³ط¢طŒأ—آ³أ¢â‚¬â€‌أ—آ³ط¢آ¨ أ—آ³ط¢آ©أ—آ³ط¢إ“ أ—آ³أ¢â‚¬â€Œأ—آ³ط¢â€چأ—آ³ط¢آ©أ—آ³ط£â€”أ—آ³ط¢â€چأ—آ³ط¢آ© (sim / hybrid / real).
    """
    new_mode = normalize_trade_mode(new_mode)

    settings = await get_or_create_settings(session, user)
    settings.trade_mode = new_mode

    session.add(settings)
    await session.commit()
    await session.refresh(settings)

    logger.info(
        "User %s trade_mode set to %s",
        user.id,
        settings.trade_mode,
    )
    return settings


def next_trade_mode(current: str | None) -> str:
    """
    أ—آ³ط¢إ“أ—آ³أ¢â‚¬آ¢أ—آ³أ¢â‚¬â„¢أ—آ³أ¢â€‍آ¢أ—آ³ط¢آ§أ—آ³أ¢â‚¬â€Œ أ—آ³ط¢â€چأ—آ³أ¢â‚¬â€‌أ—آ³أ¢â‚¬â€œأ—آ³أ¢â‚¬آ¢أ—آ³ط¢آ¨أ—آ³أ¢â€‍آ¢أ—آ³ط£â€”: sim أ—â€™أ¢â‚¬آ أ¢â‚¬â„¢ hybrid أ—â€™أ¢â‚¬آ أ¢â‚¬â„¢ real أ—â€™أ¢â‚¬آ أ¢â‚¬â„¢ sim
    """
    mode = normalize_trade_mode(current)
    if mode == "sim":
        return "hybrid"
    if mode == "hybrid":
        return "real"
    return "sim"



