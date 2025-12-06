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


# === יצירת מנוע אסינכרוני ===
engine: AsyncEngine = create_async_engine(
    settings.DATABASE_URL,
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
    תלוי שימוש ב-FastAPI (Depends) אם נרצה בהמשך.
    כרגע זה שירות עזר – נשאיר מוכן.
    """
    async with async_session_maker() as session:
        yield session


async def init_db() -> None:
    """
    הפעלת המיגרציה הבסיסית – יצירת הטבלאות לפי Base.metadata.
    נקרא מתוך main.py בזמן on_startup.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
