from decimal import Decimal
from typing import Literal
from .market_data import get_price


async def open_sim_position(
    user_id: int,
    symbol: str,
    side: Literal["long", "short"],
    amount: Decimal,
    leverage: int = 1,
) -> dict:
    entry_price = await get_price(symbol)
    return {
        "position_id": 1,
        "symbol": symbol,
        "side": side,
        "amount": str(amount),
        "leverage": leverage,
        "entry_price": str(entry_price),
    }
