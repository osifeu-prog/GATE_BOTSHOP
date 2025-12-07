from __future__ import annotations

from typing import Tuple

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.trades import Trade
from app.models.daily_stats import DailyStats
from app.models.wallets import Wallet


async def user_pnl_and_volatility(session: AsyncSession, user_id: int) -> Tuple[float, float]:
    # Placeholder  assumes Trade.amount as proxy PnL
    result = await session.execute(
        select(func.sum(Trade.amount), func.count(Trade.id)).where(Trade.user_id == user_id)
    )
    total_pnl, count = result.first() or (0.0, 0)
    total_pnl = float(total_pnl or 0.0)
    count = int(count or 0)

    if count <= 1:
        return total_pnl, 0.0

    # Simplified volatility proxy (DEMO ONLY)
    avg = total_pnl / count
    vol = abs(avg)
    return total_pnl, vol


async def compute_user_sharpe(session: AsyncSession, user_id: int) -> float:
    pnl, vol = await user_pnl_and_volatility(session, user_id)
    if vol == 0:
        return 0.0
    return pnl / vol


async def global_tvl_and_users(session: AsyncSession) -> dict:
    latest_stats = await session.execute(
        DailyStats.__table__.select().order_by(DailyStats.id.desc()).limit(1)
    )
    stats = latest_stats.scalar_one_or_none()

    total_tvl = float(stats.tvl) if stats and stats.tvl is not None else 0.0

    result_users = await session.execute(
        select(func.count(Wallet.id))
    )
    users_with_wallets = result_users.scalar_one() or 0

    return {
        "tvl": total_tvl,
        "wallets": int(users_with_wallets),
    }
