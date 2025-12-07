from sqlalchemy import Column, Integer, String, DateTime, Float
from sqlalchemy.sql import func

from app.database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=True)
    action = Column(String, nullable=False)
    details = Column(String, nullable=True)
    amount = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
