from sqlalchemy import Column, Integer, Float, DateTime, String
from sqlalchemy.sql import func

from app.database import Base


class StakingPosition(Base):
    __tablename__ = "staking_positions"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)

    amount = Column(Float, nullable=False)
    days = Column(Integer, nullable=False)
    apy = Column(Float, default=0.0)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    unlock_at = Column(DateTime(timezone=True), nullable=False)

    status = Column(String, default="active")  # active / closed
