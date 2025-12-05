from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl


class Settings(BaseSettings):
    BOT_TOKEN: str
    WEBHOOK_URL: AnyHttpUrl
    DATABASE_URL: str

    ADMIN_USER_ID: int | None = None
    MAIN_COMMUNITY_GROUP: str | None = None
    PAYMENT_CONFIRMATION_GROUP: str | None = None
    MAIN_GROUP_LINK: str | None = None

    OPENAI_API_KEY: str | None = None
    HF_TOKEN: str | None = None

    DEFAULT_TRADE_MODE: str = "sim"          # real | sim | hybrid
    DEFAULT_NETWORK: str = "testnet"         # testnet | mainnet
    DEFAULT_BASE_CURRENCY: str = "TON"       # TON | USDT | SLH

    FEE_REAL: float = 0.18
    FEE_SIM: float = 0.10
    FEE_HYBRID_REAL: float = 0.18
    FEE_HYBRID_SIM: float = 0.10

    TELEGRAM_WEBHOOK_PATH: str = "/webhook/telegram"
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
