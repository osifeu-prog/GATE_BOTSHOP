from __future__ import annotations

import logging
from decimal import Decimal
from typing import Iterable, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.user import User
from ..models.wallet import Wallet

logger = logging.getLogger("gate_botshop_ai.wallet_service")


DEFAULT_INTERNAL_BALANCE = Decimal("0")


async def get_user_wallets(
    session: AsyncSession,
    user: User,
) -> List[Wallet]:
    stmt = select(Wallet).where(Wallet.user_id == user.id)
    result = await session.execute(stmt)
    return list(result.scalars())


async def get_or_create_default_wallets(
    session: AsyncSession,
    user: User,
) -> List[Wallet]:
    """
    דואג שלכל משתמש יהיו לפחות 3 ארנקים פנימיים:

    - internal_sim_usd  (סימולציה)
    - internal_real_usd (מסחר אמיתי off-chain / future mapping)
    - internal_slh      (טוקן SLH פנימי)

    בהמשך נוכל להוסיף ארנקי TON per-user.
    """
    wallets = await get_user_wallets(session, user)
    kinds = {w.kind for w in wallets}

    missing = []

    if "internal_sim_usd" not in kinds:
        missing.append(
            Wallet(
                user_id=user.id,
                network="internal",
                kind="internal_sim_usd",
                address=None,
                encrypted_private_key=None,
                balance_ton=Decimal("0"),
                balance_usdt=DEFAULT_INTERNAL_BALANCE,
                balance_slh=Decimal("0"),
                is_primary=False,
            )
        )

    if "internal_real_usd" not in kinds:
        missing.append(
            Wallet(
                user_id=user.id,
                network="internal",
                kind="internal_real_usd",
                address=None,
                encrypted_private_key=None,
                balance_ton=Decimal("0"),
                balance_usdt=DEFAULT_INTERNAL_BALANCE,
                balance_slh=Decimal("0"),
                is_primary=True,
            )
        )

    if "internal_slh" not in kinds:
        missing.append(
            Wallet(
                user_id=user.id,
                network="internal",
                kind="internal_slh",
                address=None,
                encrypted_private_key=None,
                balance_ton=Decimal("0"),
                balance_usdt=Decimal("0"),
                balance_slh=DEFAULT_INTERNAL_BALANCE,
                is_primary=False,
            )
        )

    if missing:
        session.add_all(missing)
        await session.commit()
        logger.info(
            "Created %d default wallets for user_id=%s",
            len(missing),
            user.id,
        )
        # טוענים מחדש כולל החדשים
        wallets = await get_user_wallets(session, user)

    return wallets


def pick_wallet_by_kind(
    wallets: Iterable[Wallet],
    kind: str,
) -> Optional[Wallet]:
    for w in wallets:
        if w.kind == kind:
            return w
    return None
