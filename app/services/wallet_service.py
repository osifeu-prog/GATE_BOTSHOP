from __future__ import annotations

from decimal import Decimal
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.wallet import Wallet
from ..models.user import User
from ..models.user_settings import UserSettings
from ..config import settings


async def get_or_create_default_wallets(
    session: AsyncSession,
    user: User,
    user_settings: UserSettings,
) -> Sequence[Wallet]:
    """
    יוצר למשתמש 3 ארנקים:
    - internal demo  (לסימולציה)
    - ton_testnet   (אמיתי טסטנט)
    - ton_mainnet   (אמיתי מייננט) – בהמשך
    """

    stmt = select(Wallet).where(Wallet.user_id == user.id)
    result = await session.execute(stmt)
    wallets = list(result.scalars().all())

    if wallets:
        return wallets

    default_network = user_settings.network or "ton_testnet"

    demo_wallet = Wallet(
        user_id=user.id,
        network="testnet",
        kind="demo",
        balance_ton=Decimal("0"),
        balance_usdt=Decimal("0"),
        balance_slh=Decimal("0"),
        is_primary=False,
    )
    session.add(demo_wallet)

    real_testnet_wallet = Wallet(
        user_id=user.id,
        network=default_network,
        kind="real",
        balance_ton=Decimal("0"),
        balance_usdt=Decimal("0"),
        balance_slh=Decimal("0"),
        is_primary=True,
    )
    session.add(real_testnet_wallet)

    await session.flush()
    wallets.extend([demo_wallet, real_testnet_wallet])
    return wallets
