from __future__ import annotations

import json
import logging
import re
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..models.ton_deposits import TonDeposit
from ..models.user import User
from ..models.wallet import Wallet
from .ton_client import TONNetwork, get_recent_transactions, get_ton_price_usd

logger = logging.getLogger("gate_botshop_ai.deposit_watcher")

UID_PATTERN = re.compile(r"UID:(\d+)")


async def _find_user_by_telegram_id(
    session: AsyncSession,
    telegram_id: int,
) -> Optional[User]:
    stmt = select(User).where(User.telegram_id == telegram_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def _wallet_for_user_real_usd(
    session: AsyncSession,
    user: User,
) -> Optional[Wallet]:
    stmt = select(Wallet).where(
        Wallet.user_id == user.id,
        Wallet.kind == "internal_real_usd",
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def scan_and_credit_ton_deposits(
    session: AsyncSession,
    network: TONNetwork = "mainnet",
    limit: int = 20,
) -> int:
    if not settings.TON_TREASURY_ADDRESS:
        logger.warning("TON_TREASURY_ADDRESS not configured, skipping scan.")
        return 0

    address = settings.TON_TREASURY_ADDRESS

    txs = await get_recent_transactions(network, address, limit=limit)
    if not txs:
        return 0

    inserted = 0

    for tx in txs:
        tx_id = tx.get("transaction_id") or {}
        lt = str(tx_id.get("lt", ""))
        h = str(tx_id.get("hash", ""))

        if not lt or not h:
            continue

        stmt = select(TonDeposit).where(
            TonDeposit.tx_lt == lt,
            TonDeposit.tx_hash == h,
            TonDeposit.network == network,
        )
        res = await session.execute(stmt)
        if res.scalar_one_or_none() is not None:
            continue

        in_msg = tx.get("in_msg") or {}
        value_str = in_msg.get("value") or "0"
        comment = in_msg.get("message") or in_msg.get("msg_data", "")

        try:
            nano = Decimal(value_str)
        except Exception:
            nano = Decimal("0")

        if nano <= 0:
            continue

        amount_ton = nano / Decimal("1_000_000_000")

        m = UID_PATTERN.search(comment or "")
        telegram_id: Optional[int] = int(m.group(1)) if m else None

        deposit = TonDeposit(
            tx_lt=lt,
            tx_hash=h,
            direction="in",
            treasury_address=address,
            network=network,
            amount_ton=amount_ton,
            comment=comment,
            created_at=datetime.utcfromtimestamp(tx.get("utime", 0)),
            raw_json=json.dumps(tx),
        )

        user: Optional[User] = None
        if telegram_id is not None:
            user = await _find_user_by_telegram_id(session, telegram_id)

        if user is not None:
            deposit.user_id = user.id

            wallet = await _wallet_for_user_real_usd(session, user)
            if wallet is not None:
                ton_price = await get_ton_price_usd()
                wallet.balance_usdt += amount_ton * ton_price
                deposit.credited = True
                deposit.processed_at = datetime.utcnow()

        session.add(deposit)
        inserted += 1

    if inserted:
        await session.commit()
        logger.info("Recorded %d new TON deposits (%s).", inserted, network)

    return inserted
