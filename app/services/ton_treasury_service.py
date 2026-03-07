أ—ع؛ط¢آ»ط¢طںfrom decimal import Decimal

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.daily_stats import DailyStats

TON_DECIMALS = Decimal("1000000000")  # 1e9 nanoton per TON


async def get_treasury_balance_ton() -> Decimal:
    """
    أ—آ³ط¢آ§أ—آ³ط¢آ¨أ—آ³أ¢â€‍آ¢أ—آ³ط¢ع¯أ—آ³ط£â€” أ—آ³أ¢â€‍آ¢أ—آ³ط£â€”أ—آ³ط¢آ¨أ—آ³ط£â€” أ—آ³أ¢â‚¬â€Œأ—آ³ط¢آ§أ—آ³أ¢â‚¬آ¢أ—آ³أ¢â€ڑع¾أ—آ³أ¢â‚¬â€Œ أ—آ³أ¢â‚¬â€Œأ—آ³ط¢آ¨أ—آ³ط¢ع¯أ—آ³ط¢آ©أ—آ³أ¢â€‍آ¢أ—آ³ط£â€” أ—آ³ط¢â€چ-TonCenter (أ—آ³ط¢آ§أ—آ³ط¢آ¨أ—آ³أ¢â€‍آ¢أ—آ³ط¢ع¯أ—آ³أ¢â‚¬â€Œ أ—آ³أ¢â‚¬ع©أ—آ³ط¢إ“أ—آ³أ¢â‚¬ع©أ—آ³أ¢â‚¬إ“).
    أ—آ³ط¢ع¯أ—آ³ط¢â€Œ أ—آ³ط¢ع¯أ—آ³أ¢â€‍آ¢أ—آ³ط¢ع؛ أ—آ³ط¢آ§أ—آ³أ¢â‚¬آ¢أ—آ³ط¢آ أ—آ³أ¢â€ڑع¾أ—آ³أ¢â€‍آ¢أ—آ³أ¢â‚¬â„¢ أ—آ³ط¢â€چأ—آ³ط¢إ“أ—آ³ط¢ع¯  أ—آ³ط¢â€چأ—آ³أ¢â‚¬â€‌أ—آ³أ¢â‚¬â€œأ—آ³أ¢â€‍آ¢أ—آ³ط¢آ¨ 0 أ—آ³أ¢â‚¬ع©أ—آ³ط¢â€چأ—آ³ط¢آ§أ—آ³أ¢â‚¬آ¢أ—آ³ط¢â€Œ أ—آ³ط¢إ“أ—آ³أ¢â‚¬â€Œأ—آ³أ¢â€ڑع¾أ—آ³أ¢â€‍آ¢أ—آ³ط¢إ“ أ—آ³ط¢ع¯أ—آ³ط£â€” أ—آ³أ¢â‚¬â€Œأ—آ³ط¢آ©أ—آ³ط¢آ¨أ—آ³ط£â€”.
    """
    address = settings.TON_TREASURY_ADDRESS
    endpoint = settings.TON_MAINNET_API_ENDPOINT
    api_key = settings.TON_MAINNET_API_KEY

    # أ—آ³ط¢ع¯أ—آ³ط¢â€Œ أ—آ³ط¢ع¯أ—آ³أ¢â€‍آ¢أ—آ³ط¢ع؛ أ—آ³أ¢â‚¬ط›أ—آ³ط£â€”أ—آ³أ¢â‚¬آ¢أ—آ³أ¢â‚¬ع©أ—آ³ط£â€”  أ—آ³أ¢â‚¬â€‌أ—آ³أ¢â‚¬آ¢أ—آ³أ¢â‚¬â€œأ—آ³ط¢آ¨أ—آ³أ¢â€‍آ¢أ—آ³ط¢â€Œ 0 أ—آ³أ¢â‚¬ط›أ—آ³أ¢â‚¬إ“أ—آ³أ¢â€‍آ¢ أ—آ³ط¢آ©أ—آ³أ¢â‚¬â€Œأ—آ³ط¢â€چأ—آ³ط¢آ¢أ—آ³ط¢آ¨أ—آ³أ¢â‚¬ط›أ—آ³ط£â€” أ—آ³ط£â€”أ—آ³أ¢â€‍آ¢أ—آ³ط¢آ©أ—آ³ط¢ع¯أ—آ³ط¢آ¨ أ—آ³أ¢â€‍آ¢أ—آ³ط¢آ¦أ—آ³أ¢â€‍آ¢أ—آ³أ¢â‚¬ع©أ—آ³أ¢â‚¬â€Œ
    if not address:
        return Decimal("0")

    payload = {
        "id": 1,
        "jsonrpc": "2.0",
        "method": "getAddressBalance",
        "params": {"address": address},
    }

    headers: dict[str, str] = {}
    if api_key:
        headers["X-API-Key"] = api_key

    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.post(endpoint, json=payload, headers=headers)
        r.raise_for_status()
        data = r.json()

    if "result" not in data:
        return Decimal("0")

    raw_balance = Decimal(data["result"])
    return raw_balance / TON_DECIMALS


async def update_daily_tvl(session: AsyncSession) -> DailyStats:
    """
    أ—آ³أ¢â€‍آ¢أ—آ³أ¢â‚¬آ¢أ—آ³ط¢آ¦أ—آ³ط¢آ¨ أ—آ³ط¢آ¨أ—آ³ط¢آ©أ—آ³أ¢â‚¬آ¢أ—آ³ط¢â€چأ—آ³ط£â€” DailyStats أ—آ³ط¢إ“أ—آ³أ¢â€ڑع¾أ—آ³أ¢â€‍آ¢ أ—آ³أ¢â€‍آ¢أ—آ³ط£â€”أ—آ³ط¢آ¨أ—آ³ط£â€” أ—آ³أ¢â‚¬â€Œ-TON أ—آ³أ¢â‚¬ع©أ—آ³ط¢آ§أ—آ³أ¢â‚¬آ¢أ—آ³أ¢â€ڑع¾أ—آ³أ¢â‚¬â€Œ (TVL).
    أ—آ³أ¢â‚¬ط›أ—آ³ط¢آ¨أ—آ³أ¢â‚¬â„¢أ—آ³ط¢آ¢: TVL = أ—آ³أ¢â€‍آ¢أ—آ³ط£â€”أ—آ³ط¢آ¨أ—آ³ط£â€” TON أ—آ³أ¢â‚¬ع©أ—آ³ط¢إ“أ—آ³أ¢â‚¬ع©أ—آ³أ¢â‚¬إ“.
    """
    balance_ton = await get_treasury_balance_ton()

    stats = DailyStats(
        tvl=float(balance_ton),
        deposits=0.0,
        withdrawals=0.0,
        users_registered=0,
        trades_today=0,
    )
    session.add(stats)
    await session.commit()
    await session.refresh(stats)
    return stats



