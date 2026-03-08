import asyncio
import httpx
from telegram import Bot
from app.database import init_db, async_session_maker
from app.config import settings
from app.services.staking_engine import get_user_stakes


async def test_health():
    async with httpx.AsyncClient() as client:
        r = await client.get("http://127.0.0.1:8000/health")
        assert r.status_code == 200
        print("âœ“ Health endpoint OK")


async def test_db():
    try:
        await init_db()
        print("âœ“ Database schema OK")
    except Exception as e:
        print("âœ— Database error:", e)
        raise


async def test_webhook():
    bot = Bot(settings.BOT_TOKEN)
    me = await bot.get_me()
    assert me.username is not None
    print("âœ“ Telegram bot reachable")


async def test_start_command():
    bot = Bot(settings.BOT_TOKEN)
    me = await bot.get_me()
    print(f"âœ“ Bot identity: @{me.username}")


async def test_staking_logic():
    async with async_session_maker() as session:
        stakes = await get_user_stakes(session, telegram_user_id=settings.ADMIN_USER_ID)
        print(f"âœ“ Staking positions fetched: {len(stakes)}")


async def run_all():
    print("=== Running Smoke Tests ===")
    await test_health()
    await test_db()
    await test_webhook()
    await test_start_command()
    await test_staking_logic()
    print("=== All tests passed ===")


if __name__ == "__main__":
    asyncio.run(run_all())

