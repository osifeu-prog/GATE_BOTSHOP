from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import text

from .config import settings


class Base(DeclarativeBase):
    """Base class for all ORM models."""
    pass


def _normalize_db_url(raw: str) -> str:
    # Railway gives postgres://... – convert to asyncpg url
    if raw.startswith("postgres://"):
        raw = "postgresql://" + raw[len("postgres://"):]
    if raw.startswith("postgresql://") and "+asyncpg" not in raw:
        raw = "postgresql+asyncpg://" + raw[len("postgresql://"):]
    return raw


DATABASE_URL = _normalize_db_url(settings.DATABASE_URL)

engine = create_async_engine(DATABASE_URL, echo=False, future=True)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def init_db() -> None:
    """Create tables if needed and ensure DB connection is alive."""
    async with engine.begin() as conn:
        from . import models  # noqa: F401
        await conn.run_sync(Base.metadata.create_all)
        await conn.execute(text("SELECT 1"))
