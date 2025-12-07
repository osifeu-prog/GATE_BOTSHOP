from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # הגדרה בסגנון Pydantic v2 – קריאת משתנים מתוך .env
    model_config = SettingsConfigDict(env_file=".env")

    PROJECT_NAME: str = "GATE BOTSHOP  TON Bank"

    BOT_TOKEN: str
    ADMIN_USER_ID: int
    ADMIN_PASSWORD: str

    DATABASE_URL: str

    # TON endpoints + API keys
    # ברירות מחדל בטוחות כדי שהשרת יעלה גם בלי קונפיג מלא
    TON_MAINNET_API_ENDPOINT: str = "https://toncenter.com/api/v2/jsonRPC"
    TON_TESTNET_API_ENDPOINT: str = "https://testnet.toncenter.com/api/v2/jsonRPC"

    TON_API_KEY: str | None = None
    TON_TESTNET_API_KEY: str | None = None

    TON_TREASURY_WALLET: str | None = None
    TON_TREASURY_PRIVATE_KEY: str | None = None

    # Trading / modes
    DEFAULT_TRADE_MODE: str = "sim"  # sim / real
    MIN_STAKE_AMOUNT: float = 10.0
    MAX_STAKE_AMOUNT: float = 100000.0

    # Referral / groups
    REFERRAL_BONUS_PERCENT: float = 5.0
    MAX_REFERRAL_LEVELS: int = 3

    ADMIN_GROUP_ID: int | None = None
    SIGNALS_GROUP_ID: int | None = None
    PAYMENT_CONFIRMATION_GROUP: str | None = None
    MAIN_GROUP_LINK: str | None = None

    # AI systems (optional)
    OPENAI_API_KEY: str | None = None
    HF_TOKEN: str | None = None

    WEBHOOK_URL: str
    TELEGRAM_WEBHOOK_PATH: str = "/webhook/telegram"

    LOG_LEVEL: str = "INFO"


settings = Settings()
