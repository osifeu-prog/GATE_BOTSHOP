from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base


class StakePosition(Base):
    __tablename__ = "stakes"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    is_demo: Mapped[bool] = mapped_column(Boolean, default=True, index=True)

    amount_slh: Mapped[float] = mapped_column(Float)
    lock_days: Mapped[int] = mapped_column(Integer)
    apy: Mapped[float] = mapped_column(Float)

    active: Mapped[bool] = mapped_column(Boolean, default=True)

    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    ends_at: Mapped[datetime] = mapped_column(DateTime)
    last_yield_calculated_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )

    user = relationship("User", back_populates="stakes")
