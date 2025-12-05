from datetime import datetime
from typing import Optional

from sqlalchemy import String, BigInteger, Integer, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    username: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    first_name: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    xp: Mapped[int] = mapped_column(Integer, default=0)
    level: Mapped[str] = mapped_column(String(32), default="Beginner")
    membership_tier: Mapped[str] = mapped_column(String(32), default="Free")

    mode: Mapped[str] = mapped_column(String(8), default="demo")  # demo/real

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    wallets = relationship("Wallet", back_populates="user")
    stakes = relationship("StakePosition", back_populates="user")
    referrals_from = relationship(
        "ReferralRelation",
        foreign_keys="ReferralRelation.parent_id",
        back_populates="parent",
    )
    referrals_to = relationship(
        "ReferralRelation",
        foreign_keys="ReferralRelation.child_id",
        back_populates="child",
    )
