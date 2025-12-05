from __future__ import annotations

from typing import List, Dict, Any
import httpx

BINANCE_REST = "https://api.binance.com"


async def fetch_klines_binance(symbol: str, interval: str = "15m", limit: int = 200) -> List[Dict[str, Any]]:
    """Fetch recent OHLCV candles from Binance.

    Returns a list of dicts with keys: open_time, open, high, low, close, volume.
    """
    params = {"symbol": symbol.upper(), "interval": interval, "limit": limit}
    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.get(f"{BINANCE_REST}/api/v3/klines", params=params)
        r.raise_for_status()
        raw = r.json()

    candles: List[Dict[str, Any]] = []
    for row in raw:
        candles.append(
            {
                "open_time": row[0],
                "open": float(row[1]),
                "high": float(row[2]),
                "low": float(row[3]),
                "close": float(row[4]),
                "volume": float(row[5]),
            }
        )
    return candles


async def fetch_ticker_binance(symbol: str) -> float:
    """Return the last price for symbol from Binance."""
    params = {"symbol": symbol.upper()}
    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.get(f"{BINANCE_REST}/api/v3/ticker/price", params=params)
        r.raise_for_status()
        data = r.json()
    return float(data["price"])
