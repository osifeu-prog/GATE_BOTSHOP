from typing import Any


async def get_price(symbol: str) -> float:
    """Placeholder only – integrate real market APIs later."""
    symbol = symbol.upper()
    if symbol.endswith("USDT"):
        return 100.0
    return 1.0


async def get_full_ticker(symbol: str) -> dict[str, Any]:
    price = await get_price(symbol)
    return {
        "symbol": symbol.upper(),
        "price": price,
        "source": "placeholder",
    }
