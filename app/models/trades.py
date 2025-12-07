from sqlalchemy import Column, Integer, Float, String, DateTime
from sqlalchemy.sql import func
from app.database import Base

class Trade(Base):
    __tablename__ = "trades"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)

    symbol = Column(String)
    position = Column(String)   # long / short
    amount = Column(Float, default=0.0)
    leverage = Column(Integer, default=1)

    entry_price = Column(Float)
    exit_price = Column(Float, nullable=True)

    status = Column(String, default="open")  # open / closed
    created_at = Column(DateTime(timezone=True), server_default=func.now())
