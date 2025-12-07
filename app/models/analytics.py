from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy import Integer, String, Date, Numeric
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


class DailyStats(Base):
    __tablename__ = "daily_stats"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    day: Mapped[date] = mapped_column(Date, unique=True, index=True)

    active_users: Mapped[int] = mapped_column(Integer, default=0)
    trades_count: Mapped[int] = mapped_column(Integer, default=0)
    p2p_orders_count: Mapped[int] = mapped_column(Integer, default=0)
    volume_ton: Mapped[Decimal] = mapped_column(Numeric(38, 9), default=Decimal("0"))
