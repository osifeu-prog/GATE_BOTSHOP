import httpx
from typing import Dict, Any, List


async def fetch_binance_klines(symbol: str, interval: str = "15m", limit: int = 200) -> List[List[Any]]:
    url = "https://api.binance.com/api/v3/klines"
    params = {"symbol": symbol, "interval": interval, "limit": limit}
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(url, params=params)
        r.raise_for_status()
        return r.json()


async def fetch_binance_price(symbol: str) -> float:
    url = "https://api.binance.com/api/v3/ticker/price"
    params = {"symbol": symbol}
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(url, params=params)
        r.raise_for_status()
        data = r.json()
        return float(data["price"])
