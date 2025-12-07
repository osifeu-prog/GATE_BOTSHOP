from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession  # noqa: F401

from .ton_client import get_ton_price_usd, get_treasury_balances


@dataclass
class TVLSnapshot:
    tvl_ton: Decimal
    tvl_usd: Decimal
    risk_band: str


async def compute_ton_tvl_snapshot(session: AsyncSession) -> Optional[TVLSnapshot]:  # noqa: ARG001
    balances = await get_treasury_balances()

    total_ton = Decimal("0")
    for v in balances.values():
        if v is not None:
            total_ton += v

    if total_ton == 0:
        return None

    ton_price = await get_ton_price_usd()
    tvl_usd = total_ton * ton_price

    if tvl_usd < Decimal("1000"):
        band = "Low"
    elif tvl_usd < Decimal("10000"):
        band = "Medium"
    else:
        band = "High"

    return TVLSnapshot(tvl_ton=total_ton, tvl_usd=tvl_usd, risk_band=band)
