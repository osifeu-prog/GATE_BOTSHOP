from sqlalchemy import Column, Integer, Float, String, DateTime
from sqlalchemy.sql import func

from app.database import Base


class Wallet(Base):
    __tablename__ = "wallets"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)

    balance_sim = Column(Float, default=0.0)   # סימולציה
    balance_real = Column(Float, default=0.0)  # חוב פנימי "אמיתי"
    balance_slh = Column(Float, default=0.0)   # SLH פנימי

    ton_mainnet = Column(String, nullable=True)
    ton_testnet = Column(String, nullable=True)

    updated_at = Column(
        DateTime(timezone=True),
        onupdate=func.now(),
        server_default=func.now(),
    )
