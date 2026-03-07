from sqlalchemy.ext.asyncio import AsyncSession

from app.models.users import User

ALLOWED_ACTIONS = {
    "noncustodial": [],  # أ—آ³ط¢إ“أ—آ³ط¢ع¯ أ—آ³ط¢â€چأ—آ³ط¢ع¯أ—آ³أ¢â€ڑع¾أ—آ³ط¢آ©أ—آ³ط¢آ¨ أ—آ³أ¢â‚¬â€Œأ—آ³أ¢â€ڑع¾أ—آ³ط¢آ§أ—آ³أ¢â‚¬إ“أ—آ³أ¢â‚¬آ¢أ—آ³ط£â€”/أ—آ³ط¢طŒأ—آ³ط«إ“أ—آ³أ¢â€‍آ¢أ—آ³أ¢â€‍آ¢أ—آ³ط¢آ§أ—آ³أ¢â€‍آ¢أ—آ³ط¢آ أ—آ³أ¢â‚¬â„¢ أ—آ³أ¢â€ڑع¾أ—آ³ط¢آ أ—آ³أ¢â€‍آ¢أ—آ³ط¢â€چأ—آ³أ¢â€‍آ¢أ—آ³أ¢â€‍آ¢أ—آ³ط¢â€Œ
    "custodial": ["deposit", "withdraw", "stake", "credit"],
    "hybrid": ["deposit", "stake"],
}


async def get_investment_mode(session: AsyncSession, user_id: int) -> str:
    user = await session.get(User, user_id)
    if not user:
        return "noncustodial"
    return user.investment_mode or "noncustodial"


async def can_perform(session: AsyncSession, user_id: int, action: str) -> bool:
    mode = await get_investment_mode(session, user_id)
    return action in ALLOWED_ACTIONS.get(mode, [])


async def enforce_or_reject(session: AsyncSession, user_id: int, action: str) -> bool:
    allowed = await can_perform(session, user_id, action)
    mode = await get_investment_mode(session, user_id)

    if not allowed:
        if mode == "noncustodial":
            raise Exception("أ—آ³أ¢â‚¬â€Œأ—آ³أ¢â‚¬â€‌أ—آ³ط¢آ©أ—آ³أ¢â‚¬ع©أ—آ³أ¢â‚¬آ¢أ—آ³ط¢ع؛ أ—آ³ط¢â€چأ—آ³أ¢â‚¬آ¢أ—آ³أ¢â‚¬â„¢أ—آ³أ¢â‚¬إ“أ—آ³ط¢آ¨ Non-Custodial  أ—آ³ط¢ع¯أ—آ³أ¢â€‍آ¢أ—آ³ط¢ع؛ أ—آ³ط¢آ©أ—آ³أ¢â€‍آ¢أ—آ³ط¢آ أ—آ³أ¢â‚¬آ¢أ—آ³أ¢â€‍آ¢ أ—آ³أ¢â‚¬ع©أ—آ³أ¢â€‍آ¢أ—آ³ط£â€”أ—آ³ط¢آ¨أ—آ³أ¢â‚¬آ¢أ—آ³ط£â€” أ—آ³أ¢â€ڑع¾أ—آ³ط¢آ أ—آ³أ¢â€‍آ¢أ—آ³ط¢â€چأ—آ³أ¢â€‍آ¢أ—آ³أ¢â‚¬آ¢أ—آ³ط£â€”.")
        if mode == "hybrid":
            raise Exception("أ—آ³أ¢â‚¬ع©أ—آ³ط¢â€چأ—آ³ط¢آ¦أ—آ³أ¢â‚¬ع© Hybrid أ—آ³أ¢â€ڑع¾أ—آ³ط¢آ¢أ—آ³أ¢â‚¬آ¢أ—آ³ط¢إ“أ—آ³أ¢â‚¬â€Œ أ—آ³أ¢â‚¬â€œأ—آ³أ¢â‚¬آ¢ أ—آ³أ¢â‚¬إ“أ—آ³أ¢â‚¬آ¢أ—آ³ط¢آ¨أ—آ³ط¢آ©أ—آ³ط£â€” أ—آ³ط¢ع¯أ—آ³أ¢â€‍آ¢أ—آ³ط¢آ©أ—آ³أ¢â‚¬آ¢أ—آ³ط¢آ¨ أ—آ³ط¢â€چأ—آ³أ¢â€ڑع¾أ—آ³أ¢â‚¬آ¢أ—آ³ط¢آ¨أ—آ³ط¢آ© أ—آ³ط¢ع¯أ—آ³أ¢â‚¬آ¢ أ—آ³ط¢â€چأ—آ³ط¢طŒأ—آ³ط¢إ“أ—آ³أ¢â‚¬آ¢أ—آ³ط¢إ“ أ—آ³ط¢ع¯أ—آ³أ¢â‚¬â€‌أ—آ³ط¢آ¨.")
        raise Exception("أ—آ³أ¢â‚¬â€Œأ—آ³أ¢â€ڑع¾أ—آ³ط¢آ¢أ—آ³أ¢â‚¬آ¢أ—آ³ط¢إ“أ—آ³أ¢â‚¬â€Œ أ—آ³ط¢ع¯أ—آ³أ¢â€‍آ¢أ—آ³ط¢آ أ—آ³أ¢â‚¬â€Œ أ—آ³ط¢â€چأ—آ³أ¢â‚¬آ¢أ—آ³ط£â€”أ—آ³ط¢آ¨أ—آ³ط£â€” أ—آ³ط¢إ“أ—آ³أ¢â€ڑع¾أ—آ³أ¢â€‍آ¢ أ—آ³ط¢â€چأ—آ³ط¢آ¦أ—آ³أ¢â‚¬ع© أ—آ³أ¢â‚¬â€Œأ—آ³أ¢â‚¬â€‌أ—آ³ط¢آ©أ—آ³أ¢â‚¬ع©أ—آ³أ¢â‚¬آ¢أ—آ³ط¢ع؛.")

    return True




