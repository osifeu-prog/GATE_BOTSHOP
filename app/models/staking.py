from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import Integer, String, Numeric, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


class StakingPosition(Base):
    """
    أ—آ³ط«إ“أ—آ³أ¢â‚¬ع©أ—آ³ط¢إ“أ—آ³ط£â€” أ—آ³أ¢â‚¬â€‌أ—آ³أ¢â€‍آ¢أ—آ³ط¢طŒأ—آ³أ¢â‚¬ط›أ—آ³أ¢â‚¬آ¢أ—آ³ط¢ع؛ (أ—آ³ط¢طŒأ—آ³ط«إ“أ—آ³أ¢â€‍آ¢أ—آ³أ¢â€‍آ¢أ—آ³ط¢آ§أ—آ³أ¢â€‍آ¢أ—آ³ط¢آ أ—آ³أ¢â‚¬â„¢) أ—آ³أ¢â‚¬ع©-SLH.
    أ—آ³أ¢â‚¬ط›أ—آ³ط¢إ“ أ—آ³ط¢آ¨أ—آ³ط¢آ©أ—آ³أ¢â‚¬آ¢أ—آ³ط¢â€چأ—آ³أ¢â‚¬â€Œ أ—آ³ط¢â€چأ—آ³أ¢â€‍آ¢أ—آ³أ¢â€‍آ¢أ—آ³ط¢آ¦أ—آ³أ¢â‚¬â„¢أ—آ³ط£â€” أ—آ³أ¢â‚¬â€‌أ—آ³أ¢â€‍آ¢أ—آ³ط¢طŒأ—آ³أ¢â‚¬ط›أ—آ³أ¢â‚¬آ¢أ—آ³ط¢ع؛ أ—آ³ط¢ع¯أ—آ³أ¢â‚¬â€‌أ—آ³أ¢â‚¬إ“ أ—آ³ط¢إ“أ—آ³ط¢â€چأ—آ³ط¢آ©أ—آ³ط£â€”أ—آ³ط¢â€چأ—آ³ط¢آ© أ—آ³ط«إ“أ—آ³ط¢إ“أ—آ³أ¢â‚¬â„¢أ—آ³ط¢آ¨أ—آ³ط¢â€Œ.
    """

    __tablename__ = "staking_positions"

    # أ—آ³ط¢â€چأ—آ³أ¢â‚¬â€œأ—آ³أ¢â‚¬â€Œأ—آ³أ¢â‚¬â€Œ أ—آ³أ¢â€ڑع¾أ—آ³ط¢آ أ—آ³أ¢â€‍آ¢أ—آ³ط¢â€چأ—آ³أ¢â€‍آ¢ أ—آ³ط¢آ©أ—آ³ط¢إ“ أ—آ³أ¢â‚¬â€Œأ—آ³أ¢â‚¬â€‌أ—آ³أ¢â€‍آ¢أ—آ³ط¢طŒأ—آ³أ¢â‚¬ط›أ—آ³أ¢â‚¬آ¢أ—آ³ط¢ع؛
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    # أ—آ³ط¢â€چأ—آ³أ¢â‚¬â€œأ—آ³أ¢â‚¬â€Œأ—آ³أ¢â‚¬â€Œ أ—آ³أ¢â‚¬â€Œأ—آ³ط¢â€چأ—آ³ط¢آ©أ—آ³ط£â€”أ—آ³ط¢â€چأ—آ³ط¢آ© (Telegram user_id)
    telegram_user_id: Mapped[int] = mapped_column(
        Integer,
        index=True,
        nullable=False,
    )

    # أ—آ³ط¢طŒأ—آ³أ¢â‚¬ط›أ—آ³أ¢â‚¬آ¢أ—آ³ط¢â€Œ أ—آ³أ¢â‚¬â€Œأ—آ³ط¢آ§أ—آ³ط¢آ¨أ—آ³ط¢ع؛ أ—آ³أ¢â‚¬ع©-SLH
    principal_slh: Mapped[Decimal] = mapped_column(
        Numeric(38, 10),
        nullable=False,
    )

    # أ—آ³ط£â€”أ—آ³ط¢آ©أ—آ³أ¢â‚¬آ¢أ—آ³ط¢ع¯أ—آ³أ¢â‚¬â€Œ أ—آ³ط¢آ¦أ—آ³أ¢â€ڑع¾أ—آ³أ¢â‚¬آ¢أ—آ³أ¢â€‍آ¢أ—آ³أ¢â‚¬â€Œ أ—آ³أ¢â‚¬ع©-SLH (أ—آ³ط¢â€چأ—آ³أ¢â‚¬â€‌أ—آ³أ¢â‚¬آ¢أ—آ³ط¢آ©أ—آ³أ¢â‚¬ع©أ—آ³ط£â€” أ—آ³أ¢â‚¬ع©أ—آ³أ¢â‚¬â€œأ—آ³ط¢â€چأ—آ³ط¢ع؛ أ—آ³أ¢â€ڑع¾أ—آ³ط£â€”أ—آ³أ¢â€‍آ¢أ—آ³أ¢â‚¬â€‌أ—آ³ط£â€” أ—آ³أ¢â‚¬â€Œأ—آ³أ¢â‚¬â€‌أ—آ³أ¢â€‍آ¢أ—آ³ط¢طŒأ—آ³أ¢â‚¬ط›أ—آ³أ¢â‚¬آ¢أ—آ³ط¢ع؛)
    expected_reward_slh: Mapped[Decimal] = mapped_column(
        Numeric(38, 10),
        nullable=False,
        default=Decimal("0"),
    )

    # أ—آ³ط¢â€چأ—آ³ط¢آ©أ—آ³ط¢ع‘ أ—آ³أ¢â‚¬â€Œأ—آ³أ¢â‚¬â€‌أ—آ³أ¢â€‍آ¢أ—آ³ط¢طŒأ—آ³أ¢â‚¬ط›أ—آ³أ¢â‚¬آ¢أ—آ³ط¢ع؛ أ—آ³أ¢â‚¬ع©أ—آ³أ¢â€‍آ¢أ—آ³ط¢â€چأ—آ³أ¢â€‍آ¢أ—آ³ط¢â€Œ
    duration_days: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    # أ—آ³ط¢طŒأ—آ³ط«إ“أ—آ³ط«إ“أ—آ³أ¢â‚¬آ¢أ—آ³ط¢طŒ: open / closed / cancelled
    status: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default="open",
        index=True,
    )

    # أ—آ³أ¢â‚¬â€œأ—آ³ط¢â€چأ—آ³ط¢ع؛ أ—آ³أ¢â€ڑع¾أ—آ³ط£â€”أ—آ³أ¢â€‍آ¢أ—آ³أ¢â‚¬â€‌أ—آ³ط£â€” أ—آ³أ¢â‚¬â€Œأ—آ³أ¢â‚¬â€‌أ—آ³أ¢â€‍آ¢أ—آ³ط¢طŒأ—آ³أ¢â‚¬ط›أ—آ³أ¢â‚¬آ¢أ—آ³ط¢ع؛
    opened_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )

    # أ—آ³أ¢â‚¬â€œأ—آ³ط¢â€چأ—آ³ط¢ع؛ أ—آ³ط¢طŒأ—آ³أ¢â€‍آ¢أ—آ³أ¢â‚¬آ¢أ—آ³ط¢â€Œ أ—آ³ط¢â€چأ—آ³ط£â€”أ—آ³أ¢â‚¬آ¢أ—آ³أ¢â‚¬ط›أ—آ³ط¢آ أ—آ³ط¢ع؛
    closes_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    # أ—آ³أ¢â‚¬â€œأ—آ³ط¢â€چأ—آ³ط¢ع؛ أ—آ³ط¢طŒأ—آ³أ¢â‚¬â„¢أ—آ³أ¢â€‍آ¢أ—آ³ط¢آ¨أ—آ³أ¢â‚¬â€Œ أ—آ³أ¢â‚¬ع©أ—آ³أ¢â€ڑع¾أ—آ³أ¢â‚¬آ¢أ—آ³ط¢آ¢أ—آ³ط¢إ“ (أ—آ³ط¢ع¯أ—آ³ط¢â€Œ أ—آ³ط¢آ أ—آ³ط¢طŒأ—آ³أ¢â‚¬â„¢أ—آ³ط¢آ¨)
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



