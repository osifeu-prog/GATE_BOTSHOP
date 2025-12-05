from sqlalchemy import Column, Integer, BigInteger, String, DateTime, func
from ..database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(BigInteger, unique=True, index=True, nullable=False)
    username = Column(String(64), nullable=True)
    first_name = Column(String(128), nullable=True)
    last_name = Column(String(128), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
