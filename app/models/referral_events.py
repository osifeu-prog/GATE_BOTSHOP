from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from app.database import Base

class ReferralEvent(Base):
    __tablename__ = "referral_events"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    event_type = Column(String, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
