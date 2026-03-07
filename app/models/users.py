from sqlalchemy import Column, BigInteger, String, DateTime, Boolean, Float, Integer
from sqlalchemy.sql import func

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True, index=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    human_score = Column(Float, default=0.0)
    trust_score = Column(Float, default=0.0)

    referral_code = Column(String, nullable=True)

    investment_mode = Column(String, default="noncustodial")
    custody_agreed = Column(Boolean, default=False)

    user_tier = Column(Integer, default=1)


