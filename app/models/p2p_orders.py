from sqlalchemy import Column, Integer, Float, String, DateTime
from sqlalchemy.sql import func
from app.database import Base

class P2POrder(Base):
    __tablename__ = "p2p_orders"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)

    order_type = Column(String)  # buy / sell
    amount = Column(Float, nullable=False)
    price = Column(Float, nullable=False)

    ton_address = Column(String)
    status = Column(String, default="open")  # open / matched / closed

    created_at = Column(DateTime(timezone=True), server_default=func.now())
