from decimal import Decimal

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.daily_stats import DailyStats

TON_DECIMALS = Decimal("1000000000")  # 1e9 nanoton per TON


async def get_treasury_balance_ton() -> Decimal:
    """
    קריאת יתרת הקופה הראשית מ-TonCenter (קריאה בלבד).
    אם אין קונפיג מלא  מחזיר 0 במקום להפיל את השרת.
    """
    address = settings.TON_TREASURY_ADDRESS
    endpoint = settings.TON_MAINNET_API_ENDPOINT
    api_key = settings.TON_MAINNET_API_KEY

    # אם אין כתובת  חוזרים 0 כדי שהמערכת תישאר יציבה
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
    יוצר רשומת DailyStats לפי יתרת ה-TON בקופה (TVL).
    כרגע: TVL = יתרת TON בלבד.
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
