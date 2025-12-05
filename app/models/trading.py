from sqlalchemy import Column, Integer, String, ForeignKey, Numeric, DateTime, func
from ..database import Base


class Trade(Base):
    __tablename__ = "trades"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True)

    mode = Column(String(16), default="sim")  # real | sim | hybrid
    symbol = Column(String(32), nullable=False)
    side = Column(String(8), nullable=False)  # buy/sell or long/short
    amount = Column(Numeric(36, 9), nullable=False)
    leverage = Column(Integer, default=1)

    entry_price = Column(Numeric(36, 9), nullable=True)
    exit_price = Column(Numeric(36, 9), nullable=True)

    status = Column(String(16), default="open")  # open / closed / liquidated

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    closed_at = Column(DateTime(timezone=True), nullable=True)
