from sqlalchemy import Column, Integer, Float, DateTime
from sqlalchemy.sql import func

from app.database import Base


class DailyStats(Base):
    __tablename__ = "daily_stats"

    id = Column(Integer, primary_key=True)

    tvl = Column(Float, default=0.0)
    deposits = Column(Float, default=0.0)
    withdrawals = Column(Float, default=0.0)

    users_registered = Column(Integer, default=0)
    trades_today = Column(Integer, default=0)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
