from __future__ import annotations

from typing import Dict, Any
import statistics
from .market_data import fetch_klines_binance
from app.schemas import TradeSignal


VALID_TIMEFRAMES = {"5m", "15m", "1h", "4h"}


async def generate_signal(symbol: str, timeframe: str = "15m") -> TradeSignal:
    """Generate a simple but structured trade signal.

    This is a heuristic baseline: it looks at recent candles and compares
    short vs long moving averages and volatility. In production you can
    replace this logic with a much more advanced model (ML, order book, etc.).
    """
    tf = timeframe if timeframe in VALID_TIMEFRAMES else "15m"

    candles = await fetch_klines_binance(symbol, tf, limit=200)
    closes = [c["close"] for c in candles]

    if len(closes) < 50:
        raise ValueError("Not enough market data to generate a signal")

    short_ma = statistics.mean(closes[-20:])
    long_ma = statistics.mean(closes[-60:])
    last_price = closes[-1]
    volatility = statistics.pstdev(closes[-60:])

    if short_ma > long_ma * 1.002:
        direction = "LONG"
    elif short_ma < long_ma * 0.998:
        direction = "SHORT"
    else:
        direction = "NEUTRAL"

    risk_perc = max(0.3, min(2.0, volatility / last_price * 100))
    rr_ratio = 2.0 if direction != "NEUTRAL" else 1.0

    if direction == "LONG":
        stop_loss = last_price * (1 - risk_perc / 100)
        take_profit = last_price * (1 + risk_perc / 100 * rr_ratio)
    elif direction == "SHORT":
        stop_loss = last_price * (1 + risk_perc / 100)
        take_profit = last_price * (1 - risk_perc / 100 * rr_ratio)
    else:
        stop_loss = last_price * 0.99
        take_profit = last_price * 1.01

    if direction == "NEUTRAL":
        confidence = 0.45
        duration_minutes = 30
    else:
        trend_strength = abs(short_ma - long_ma) / long_ma
        confidence = max(0.5, min(0.9, 0.5 + trend_strength * 10))
        duration_minutes = 30 if tf == "5m" else 90 if tf == "15m" else 240 if tf == "1h" else 480

    signal = TradeSignal(
        symbol=symbol.upper(),
        timeframe=tf,
        direction=direction,
        entry=round(last_price, 4),
        stop_loss=round(stop_loss, 4),
        take_profit=round(take_profit, 4),
        confidence=round(confidence, 3),
        risk_reward=round(rr_ratio, 2),
        estimated_duration_minutes=int(duration_minutes),
        extra={
            "short_ma": round(short_ma, 4),
            "long_ma": round(long_ma, 4),
            "volatility": round(volatility, 4),
        },
    )
    return signal
