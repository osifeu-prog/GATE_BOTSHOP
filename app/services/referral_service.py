import secrets
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.referral_links import ReferralLink
from app.models.referral_events import ReferralEvent


async def create_referral_link(session: AsyncSession, user_id: int):
    code = secrets.token_hex(4)
    link = ReferralLink(user_id=user_id, code=code)
    session.add(link)
    await session.commit()
    return code


async def log_event(session: AsyncSession, user_id: int, event: str):
    ev = ReferralEvent(user_id=user_id, event_type=event)
    session.add(ev)
    await session.commit()
