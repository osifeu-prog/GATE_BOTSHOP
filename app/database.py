from __future__ import annotations

from typing import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from .config import settings


class Base(DeclarativeBase):
    """
    בסיס משותף לכל המודלים של SQLAlchemy.
    כל המודלים יורשים ממנו: User, Wallet, Staking, P2POrder וכו'.
    """
    pass


def _build_async_db_url(raw: str) -> str:
    """
    Railway נותן בדרך כלל כתובות בסגנון:
    - postgres://...
    - postgresql://...

    אנחנו ממירים ל:
    - postgresql+asyncpg://...

    כדי ש-SQLAlchemy ישתמש בדרייבר asyncpg (ולא psycopg2).
    """
    if raw.startswith("postgres://"):
        return raw.replace("postgres://", "postgresql+asyncpg://", 1)

    if raw.startswith("postgresql://") and "+asyncpg" not in raw:
        return raw.replace("postgresql://", "postgresql+asyncpg://", 1)

    return raw


RAW_DB_URL = str(settings.DATABASE_URL)
ASYNC_DB_URL = _build_async_db_url(RAW_DB_URL)


# === יצירת מנוע אסינכרוני ===
engine: AsyncEngine = create_async_engine(
    ASYNC_DB_URL,
    echo=False,
    future=True,
)


# === מפעל סשנים אסינכרוני – זה מה שאנחנו משתמשים בו בכל המערכת ===
async_session_maker = async_sessionmaker(
    engine,
    expire_on_commit=False,
    class_=AsyncSession,
)

# שמות חלופיים למקרה שקבצים ישנים יחפשו אותם
AsyncSessionLocal = async_session_maker
async_session = async_session_maker


async def get_session() -> AsyncIterator[AsyncSession]:
    """
    פונקציית עזר (לשימוש עתידי עם Depends ב-FastAPI אם נרצה).
    כרגע לא חובה – אבל משאירים מוכנה.
    """
    async with async_session_maker() as session:
        yield session


async def init_db() -> None:
    """
    יצירת הטבלאות בבסיס הנתונים לפי Base.metadata.
    נקרא מתוך main.py בזמן on_startup.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
