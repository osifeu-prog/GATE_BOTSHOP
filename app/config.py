from typing import List, Optional, Literal, Dict
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    # === Telegram ===
    BOT_TOKEN: str
    WEBHOOK_URL: str  # e.g. https://web-production-xxxx.up.railway.app
    TELEGRAM_WEBHOOK_PATH: str = "/webhook/telegram"

    # === DB ===
    DATABASE_URL: str  # postgres://USER:PASS@HOST:PORT/DB

    # === Admin / Groups ===
    ADMIN_USER_ID: Optional[int] = None
    ADMIN_PASSWORD: Optional[str] = None
    MAIN_COMMUNITY_GROUP: Optional[str] = None
    MAIN_GROUP_LINK: Optional[str] = None
    PAYMENT_CONFIRMATION_GROUP: Optional[str] = None

    # === Trading config ===
    SUPPORTED_SYMBOLS: List[str] = [
        "BTCUSDT",
        "ETHUSDT",
        "BNBUSDT",
        "SOLUSDT",
        "XRPUSDT",
        "TONUSDT",
    ]
    DEFAULT_TIMEFRAME: str = "15m"

    # === AI ===
    AI_PROVIDER: Literal["openai", "hf"] = "openai"
    OPENAI_API_KEY: Optional[str] = None
    HF_TOKEN: Optional[str] = None
    HF_MODEL: str = "mistralai/Mixtral-8x7B-Instruct-v0.1"
    HF_API_URL: Optional[str] = None

    # === Staking plans (lock_days -> APY) ===
    STAKING_PLANS: Dict[int, float] = {
        7: 5.0,
        30: 12.0,
        90: 25.0,
    }

    # === XP & Levels ===
    LEVELS: Dict[str, int] = {
        "Beginner": 0,
        "Trader": 100,
        "Pro": 500,
        "Master": 1500,
    }

    # === Membership tiers ===
    MEMBERSHIP_TIERS: Dict[str, Dict[str, int]] = {
        "Free":  {"price_nis": 0,   "signals_per_day": 3},
        "Silver": {"price_nis": 39,  "signals_per_day": 10},
        "Gold":  {"price_nis": 98,  "signals_per_day": 25},
        "Black": {"price_nis": 444, "signals_per_day": 999},
    }

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
