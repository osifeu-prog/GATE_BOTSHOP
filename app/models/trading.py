from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import Integer, String, DateTime, Numeric, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


class Trade(Base):
    __tablename__ = "trades"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    wallet_id: Mapped[int] = mapped_column(ForeignKey("wallets.id"), index=True)

    symbol: Mapped[str] = mapped_column(String(32))
    side: Mapped[str] = mapped_column(String(4))  # buy/sell/long/short
    mode: Mapped[str] = mapped_column(String(16), default="sim")  # real/sim/hybrid

    quantity: Mapped[Decimal] = mapped_column(Numeric(38, 9))
    entry_price: Mapped[Decimal] = mapped_column(Numeric(38, 9))
    exit_price: Mapped[Decimal | None] = mapped_column(Numeric(38, 9), nullable=True)

    status: Mapped[str] = mapped_column(String(16), default="open")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
