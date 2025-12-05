from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import text

from .config import settings


class Base(DeclarativeBase):
    """Base class for all ORM models."""
    pass


def _normalize_db_url(raw: str) -> str:
    """
    Railway נותן בדרך כלל:
    postgres://user:pass@host:port/db
    או postgresql://...

    אנחנו ממירים את זה ל:
    postgresql+asyncpg://user:pass@host:port/db
    כדי להשתמש ב-asyncpg ולא ב-psycopg2.
    """
    if raw.startswith("postgres://"):
        raw = "postgresql://" + raw[len("postgres://"):]
    if raw.startswith("postgresql://") and "+asyncpg" not in raw:
        raw = "postgresql+asyncpg://" + raw[len("postgresql://"):]
    return raw


DATABASE_URL = _normalize_db_url(settings.DATABASE_URL)

engine = create_async_engine(DATABASE_URL, echo=False, future=True)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def init_db() -> None:
    """
    מחבר למסד, יוצר טבלאות אם צריך, ומוודא שהחיבור חי.
    """
    async with engine.begin() as conn:
        # לוודא שכל המודלים נרשמים לפני create_all
        from . import models  # noqa: F401

        # יצירת טבלאות אם לא קיימות
        await conn.run_sync(Base.metadata.create_all)

        # בדיקת חיבור בסיסית
        await conn.execute(text("SELECT 1"))
