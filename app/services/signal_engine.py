from __future__ import annotations

from typing import Dict, Any, List

import statistics


def simple_trend_from_klines(klines: List[List[Any]]) -> Dict[str, Any]:
    closes = [float(k[4]) for k in klines]
    if len(closes) < 20:
        return {"trend": "neutral", "volatility": 0.0}

    last = closes[-1]
    ma20 = statistics.mean(closes[-20:])
    ma50 = statistics.mean(closes[-50:]) if len(closes) >= 50 else statistics.mean(closes)

    volatility = statistics.pstdev(closes[-30:]) if len(closes) >= 30 else 0.0

    if last > ma20 > ma50:
        trend = "up"
    elif last < ma20 < ma50:
        trend = "down"
    else:
        trend = "sideways"

    return {
        "trend": trend,
        "volatility": volatility,
        "last": last,
        "ma20": ma20,
        "ma50": ma50,
    }
