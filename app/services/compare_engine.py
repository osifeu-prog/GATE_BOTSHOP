from __future__ import annotations

from typing import Dict


def compare_prices(prices: Dict[str, float]) -> str:
    if not prices:
        return "אין נתוני מחירים זמינים כרגע."

    lines = []
    base_symbol = next(iter(prices))
    base_price = prices[base_symbol]

    for name, price in prices.items():
        diff = price - base_price
        pct = (diff / base_price * 100.0) if base_price else 0.0
        lines.append(f"{name}: {price:.2f} (סטייה {pct:+.2f}%)")

    return "\n".join(lines)
