from sqlalchemy import Column, Integer, String, ForeignKey, Numeric, DateTime, func, Boolean
from ..database import Base


class StakingPosition(Base):
    __tablename__ = "staking_positions"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True)

    network = Column(String(16), default="mainnet")
    currency = Column(String(16), default="TON")
    amount = Column(Numeric(36, 9), nullable=False)

    lock_days = Column(Integer, default=30)
    apy_percent = Column(Numeric(10, 4), default=10.0)

    started_at = Column(DateTime(timezone=True), server_default=func.now())
    unlock_at = Column(DateTime(timezone=True), nullable=True)

    is_closed = Column(Boolean, default=False)
    closed_at = Column(DateTime(timezone=True), nullable=True)

    auto_redeem = Column(Boolean, default=True)
