from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base


class TonDeposit(Base):
    __tablename__ = "ton_deposits"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    tx_lt: Mapped[str] = mapped_column(String(64), index=True)
    tx_hash: Mapped[str] = mapped_column(String(128), index=True)
    direction: Mapped[str] = mapped_column(String(8), default="in")

    treasury_address: Mapped[str] = mapped_column(String(128), index=True)
    network: Mapped[str] = mapped_column(String(16), default="mainnet")

    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True,
        index=True,
    )

    amount_ton: Mapped[Decimal] = mapped_column(Numeric(38, 9))
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)

    credited: Mapped[bool] = mapped_column(Boolean, default=False, index=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    raw_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    user = relationship("User", backref="ton_deposits")
