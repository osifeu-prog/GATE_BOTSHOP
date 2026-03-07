from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base

from app.config import settings

Base = declarative_base()


def _build_async_db_url(raw: str) -> str:
    # מתקן גם postgres:// וגם postgresql://
    url = raw.replace("postgres://", "postgresql://")
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url


ASYNC_DATABASE_URL = _build_async_db_url(settings.DATABASE_URL)

engine = create_async_engine(ASYNC_DATABASE_URL, echo=False, future=True)

async_session_maker = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


async def init_db() -> None:
    # לוודא שכל המודלים נטענים לפני יצירת הטבלאות
    import app.models  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
