from decimal import Decimal
from .market_data import get_price


async def execute_dex_swap(
    user_id: int,
    from_token: str,
    to_token: str,
    amount: Decimal,
    slippage_bps: int = 50,
) -> dict:
    """Placeholder DEX swap – כאן בעתיד נחבר STON.fi / DeDust."""
    price = await get_price(f"{to_token}USDT")
    received = amount * Decimal(price)
    return {
        "tx_hash": "0xDEMOHASH",
        "from_token": from_token,
        "to_token": to_token,
        "amount_in": str(amount),
        "amount_out": str(received),
        "slippage_bps": slippage_bps,
    }
