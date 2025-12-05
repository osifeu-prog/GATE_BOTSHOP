from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from ..database import Base


class UserSettings(Base):
    __tablename__ = "user_settings"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True)

    trade_mode = Column(String(16), default="sim")      # real | sim | hybrid
    network = Column(String(16), default="testnet")     # testnet | mainnet
    base_currency = Column(String(16), default="TON")   # TON | USDT | SLH

    hybrid_mode = Column(String(16), default="ratio")   # ratio | smart | simple
    hybrid_ratio_real_percent = Column(Integer, default=50)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    user = relationship("User", backref="settings", uselist=False)
