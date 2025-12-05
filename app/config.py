import logging
from typing import List, Optional

from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    # Telegram
    BOT_TOKEN: str = Field(..., description="Telegram Bot token from BotFather")
    WEBHOOK_URL: str = Field(..., description="Public HTTPS URL for Telegram webhook")
    TELEGRAM_WEBHOOK_PATH: str = "/webhook/telegram"

    # General
    LOG_LEVEL: str = "INFO"

    # Trading symbols we explicitly support
    SUPPORTED_SYMBOLS: List[str] = [
        "BTCUSDT",
        "ETHUSDT",
        "BNBUSDT",
        "SOLUSDT",
        "XRPUSDT",
        "TONUSDT",
    ]

    # Default timeframe for signals
    DEFAULT_TIMEFRAME: str = "15m"

    # AI provider configuration
    AI_PROVIDER: str = "openai"  # options: "openai", "huggingface", "none"

    # OpenAI
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o-mini"

    # Hugging Face
    HF_TOKEN: Optional[str] = None
    HF_MODEL: str = "mistralai/Mixtral-8x7B-Instruct-v0.1"
    HF_API_URL: Optional[str] = None  # if None, built from HF_MODEL

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("gate_botshop_ai")
