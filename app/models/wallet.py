from __future__ import annotations

from decimal import Decimal

from sqlalchemy import Integer, String, Boolean, Numeric, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


class Wallet(Base):
    __tablename__ = "wallets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)

    # testnet / mainnet
    network: Mapped[str] = mapped_column(String(16), default="testnet")

    # real / demo
    kind: Mapped[str] = mapped_column(String(8), default="real")

    address: Mapped[str | None] = mapped_column(String(128), nullable=True)
    encrypted_private_key: Mapped[str | None] = mapped_column(String(512), nullable=True)

    balance_ton: Mapped[Decimal] = mapped_column(Numeric(38, 9), default=Decimal("0"))
    balance_usdt: Mapped[Decimal] = mapped_column(Numeric(38, 9), default=Decimal("0"))
    balance_slh: Mapped[Decimal] = mapped_column(Numeric(38, 9), default=Decimal("0"))

    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)
