from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import Integer, String, DateTime, Numeric, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


class RewardEvent(Base):
    __tablename__ = "reward_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    kind: Mapped[str] = mapped_column(String(32))
    amount: Mapped[Decimal] = mapped_column(Numeric(38, 9), default=Decimal("0"))
    meta: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
