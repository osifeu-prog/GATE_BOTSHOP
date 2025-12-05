from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import Integer, String, DateTime, Numeric, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


class P2POrder(Base):
    __tablename__ = "p2p_orders"

    id: Mapped[int] = mapped_column(Integer, primary key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    side: Mapped[str] = mapped_column(String(4))  # buy/sell
    currency: Mapped[str] = mapped_column(String(16), default="TON")
    price: Mapped[Decimal] = mapped_column(Numeric(38, 9))
    amount: Mapped[Decimal] = mapped_column(Numeric(38, 9))
    status: Mapped[str] = mapped_column(String(16), default="open")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
