from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import Integer, String, DateTime, Numeric, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


class P2POrder(Base):
    __tablename__ = "p2p_orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id"),
        index=True,
        nullable=False,
    )

    # buy/sell
    side: Mapped[str] = mapped_column(String(8), nullable=False)

    # TON / USDT / SLH
    base_asset: Mapped[str] = mapped_column(String(16), nullable=False)
    quote_asset: Mapped[str] = mapped_column(String(16), nullable=False)

    price: Mapped[Decimal] = mapped_column(Numeric(38, 9), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(38, 9), nullable=False)
    filled_amount: Mapped[Decimal] = mapped_column(Numeric(38, 9), default=Decimal("0"))

    # open / filled / cancelled
    status: Mapped[str] = mapped_column(String(16), default="open")

    is_testnet: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
