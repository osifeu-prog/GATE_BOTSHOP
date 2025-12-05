from sqlalchemy import Column, Integer, String, ForeignKey, Numeric, DateTime, func, Boolean
from ..database import Base


class Wallet(Base):
    __tablename__ = "wallets"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True)

    network = Column(String(16), default="testnet")  # mainnet / testnet
    kind = Column(String(16), default="real")        # real | demo

    address = Column(String(128), nullable=True)
    encrypted_private_key = Column(String(512), nullable=True)

    balance_ton = Column(Numeric(36, 9), default=0)
    balance_usdt = Column(Numeric(36, 9), default=0)
    balance_slh = Column(Numeric(36, 9), default=0)

    is_primary = Column(Boolean, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
