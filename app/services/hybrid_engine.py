from decimal import Decimal
from typing import Literal

from .dex_engine import execute_dex_swap
from .simulation_engine import open_sim_position


async def execute_hybrid_trade(
    user_id: int,
    symbol: str,
    side: Literal["long", "short"],
    total_amount: Decimal,
    real_ratio_percent: int = 50,
) -> dict:
    real_amount = total_amount * Decimal(real_ratio_percent) / Decimal(100)
    sim_amount = total_amount - real_amount

    dex_result = await execute_dex_swap(user_id, "TON", "USDT", real_amount)
    sim_result = await open_sim_position(user_id, symbol, side, sim_amount, leverage=1)

    return {
        "mode": "hybrid",
        "real_part": dex_result,
        "sim_part": sim_result,
    }
