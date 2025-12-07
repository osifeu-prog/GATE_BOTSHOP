from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float
from sqlalchemy.sql import func

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Identity / Trust
    human_score = Column(Float, default=0.0)
    trust_score = Column(Float, default=0.0)

    referral_code = Column(String, nullable=True)

    # Custody / Investment mode
    investment_mode = Column(String, default="noncustodial")  # noncustodial / custodial / hybrid
    custody_agreed = Column(Boolean, default=False)

    # Tiers
    user_tier = Column(Integer, default=1)  # 1 / 2 / 3
