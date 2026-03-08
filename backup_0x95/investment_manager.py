from sqlalchemy.ext.asyncio import AsyncSession

from app.models.users import User

ALLOWED_ACTIONS = {
    "noncustodial": [],  # ×œ×گ ×‍×گ×¤×©×¨ ×”×¤×§×“×•×ھ/×،×ک×™×™×§×™× ×’ ×¤× ×™×‍×™×™×‌
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
            raise Exception("×”×—×©×‘×•×ں ×‍×•×’×“×¨ Non-Custodial  ×گ×™×ں ×©×™× ×•×™ ×‘×™×ھ×¨×•×ھ ×¤× ×™×‍×™×•×ھ.")
        if mode == "hybrid":
            raise Exception("×‘×‍×¦×‘ Hybrid ×¤×¢×•×œ×” ×–×• ×“×•×¨×©×ھ ×گ×™×©×•×¨ ×‍×¤×•×¨×© ×گ×• ×‍×،×œ×•×œ ×گ×—×¨.")
        raise Exception("×”×¤×¢×•×œ×” ×گ×™× ×” ×‍×•×ھ×¨×ھ ×œ×¤×™ ×‍×¦×‘ ×”×—×©×‘×•×ں.")

    return True

