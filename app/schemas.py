from pydantic import BaseModel
from typing import Optional, Dict, Any


class TradeSignal(BaseModel):
    symbol: str
    timeframe: str
    direction: str  # LONG / SHORT / NEUTRAL
    entry: float
    stop_loss: float
    take_profit: float
    confidence: float
    risk_reward: float
    estimated_duration_minutes: int
    exchange_hint: Optional[str] = None
    extra: Dict[str, Any] = {}


class ExchangeQuote(BaseModel):
    exchange: str
    symbol: str
    price: float
    url: Optional[str] = None
