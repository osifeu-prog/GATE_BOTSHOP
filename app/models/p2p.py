from sqlalchemy import Column, Integer, String, ForeignKey, Numeric, DateTime, func
from ..database import Base


class P2POrder(Base):
    __tablename__ = "p2p_orders"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True)

    side = Column(String(8), nullable=False)  # buy / sell
    currency = Column(String(16), default="TON")
    price = Column(Numeric(36, 9), nullable=False)
    amount = Column(Numeric(36, 9), nullable=False)

    status = Column(String(16), default="open")  # open / matched / cancelled

    created_at = Column(DateTime(timezone=True), server_default=func.now())
