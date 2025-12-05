from __future__ import annotations

from sqlalchemy import Integer, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base


class UserSettings(Base):
    __tablename__ = "user_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)

    # real | sim | hybrid
    trade_mode: Mapped[str] = mapped_column(String(16), default="sim")

    # mainnet | testnet
    network: Mapped[str] = mapped_column(String(16), default="testnet")

    base_currency: Mapped[str] = mapped_column(String(16), default="TON")

    user = relationship("User")
