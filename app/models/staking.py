from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import Integer, String, DateTime, Numeric, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


class StakingPosition(Base):
    __tablename__ = "staking_positions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    wallet_id: Mapped[int] = mapped_column(ForeignKey("wallets.id"), index=True)

    currency: Mapped[str] = mapped_column(String(16), default="TON")
    amount: Mapped[Decimal] = mapped_column(Numeric(38, 9))
    lock_days: Mapped[int] = mapped_column(Integer, default=30)
    apy: Mapped[Decimal] = mapped_column(Numeric(10, 4), default=Decimal("0.12"))

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    unlock_at: Mapped[datetime] = mapped_column(DateTime)
    redeemed: Mapped[bool] = mapped_column(Boolean, default=False)
