from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import Integer, String, Numeric, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


class StakingPosition(Base):
    """
    ×ک×‘×œ×ھ ×—×™×،×›×•×ں (×،×ک×™×™×§×™× ×’) ×‘-SLH.
    ×›×œ ×¨×©×•×‍×” ×‍×™×™×¦×’×ھ ×—×™×،×›×•×ں ×گ×—×“ ×œ×‍×©×ھ×‍×© ×ک×œ×’×¨×‌.
    """

    __tablename__ = "staking_positions"

    # ×‍×–×”×” ×¤× ×™×‍×™ ×©×œ ×”×—×™×،×›×•×ں
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    # ×‍×–×”×” ×”×‍×©×ھ×‍×© (Telegram user_id)
    telegram_user_id: Mapped[int] = mapped_column(
        Integer,
        index=True,
        nullable=False,
    )

    # ×،×›×•×‌ ×”×§×¨×ں ×‘-SLH
    principal_slh: Mapped[Decimal] = mapped_column(
        Numeric(38, 10),
        nullable=False,
    )

    # ×ھ×©×•×گ×” ×¦×¤×•×™×” ×‘-SLH (×‍×—×•×©×‘×ھ ×‘×–×‍×ں ×¤×ھ×™×—×ھ ×”×—×™×،×›×•×ں)
    expected_reward_slh: Mapped[Decimal] = mapped_column(
        Numeric(38, 10),
        nullable=False,
        default=Decimal("0"),
    )

    # ×‍×©×ڑ ×”×—×™×،×›×•×ں ×‘×™×‍×™×‌
    duration_days: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    # ×،×ک×ک×•×،: open / closed / cancelled
    status: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default="open",
        index=True,
    )

    # ×–×‍×ں ×¤×ھ×™×—×ھ ×”×—×™×،×›×•×ں
    opened_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )

    # ×–×‍×ں ×،×™×•×‌ ×‍×ھ×•×›× ×ں
    closes_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    # ×–×‍×ں ×،×’×™×¨×” ×‘×¤×•×¢×œ (×گ×‌ × ×،×’×¨)
    closed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    def is_active(self) -> bool:
        return self.status == "open"

    def is_matured(self, now: Optional[datetime] = None) -> bool:
        now = now or datetime.utcnow()
        return now >= self.closes_at

    def __repr__(self) -> str:
        return (
            f"<StakingPosition id={self.id} tg={self.telegram_user_id} "
            f"principal={self.principal_slh} reward={self.expected_reward_slh} "
            f"status={self.status}>"
        )

