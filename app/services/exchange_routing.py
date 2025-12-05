from __future__ import annotations

from typing import List
import httpx
from app.schemas import ExchangeQuote

BINANCE_REST = "https://api.binance.com"
BYBIT_REST = "https://api.bybit.com"
OKX_REST = "https://www.okx.com"


async def _binance_price(symbol: str) -> ExchangeQuote:
    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.get(f"{BINANCE_REST}/api/v3/ticker/price", params={"symbol": symbol.upper()})
        r.raise_for_status()
        data = r.json()
    return ExchangeQuote(exchange="Binance", symbol=symbol.upper(), price=float(data["price"]), url="https://www.binance.com")


async def _bybit_price(symbol: str) -> ExchangeQuote:
    mapped = symbol.upper().replace("USDT", "USDT")
    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.get(f"{BYBIT_REST}/v5/market/tickers", params={"category": "linear", "symbol": mapped})
        r.raise_for_status()
        data = r.json()
    tickers = data.get("result", {}).get("list", [])
    if not tickers:
        raise ValueError("Symbol not found on Bybit")
    last_price = float(tickers[0]["lastPrice"])
    return ExchangeQuote(exchange="Bybit", symbol=symbol.upper(), price=last_price, url="https://www.bybit.com")


async def _okx_price(symbol: str) -> ExchangeQuote:
    mapped = symbol.upper().replace("USDT", "-USDT-SWAP")
    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.get(f"{OKX_REST}/api/v5/market/ticker", params={"instId": mapped})
        r.raise_for_status()
        data = r.json()
    tickers = data.get("data", [])
    if not tickers:
        raise ValueError("Symbol not found on OKX")
    last_price = float(tickers[0]["last"])
    return ExchangeQuote(exchange="OKX", symbol=symbol.upper(), price=last_price, url="https://www.okx.com")


async def compare_exchanges(symbol: str) -> List[ExchangeQuote]:
    """Return quotes from several exchanges to compare futures entry."""
    symbol = symbol.upper()
    quotes: List[ExchangeQuote] = []

    try:
        quotes.append(await _binance_price(symbol))
    except Exception:
        pass

    for fn in (_bybit_price, _okx_price):
        try:
            q = await fn(symbol)
            quotes.append(q)
        except Exception:
            continue

    if not quotes:
        raise ValueError("No quotes available for this symbol on supported exchanges")
    return quotes
