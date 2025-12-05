from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import Integer, String, Numeric, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


class P2POrder(Base):
    """
    מודל בסיסי להזמנות P2P.
    כרגע הוא מינימלי כדי לא לשבור כלום, ואפשר להרחיב אותו בהמשך
    (מצב, צד קנייה/מכירה, סוג נכס, רשת, וכו').
    """

    __tablename__ = "p2p_orders"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    # בעל ההזמנה (טלגרם user_id או מזהה פנימי אחר)
    owner_telegram_id: Mapped[str] = mapped_column(
        String(64),
        index=True,
        nullable=False,
    )

    # סוג פעולה: BUY / SELL
    side: Mapped[str] = mapped_column(
        String(8),
        nullable=False,
        default="BUY",
    )

    # נכס בסיס: למשל "TON", "USDT", "SLH"
    base_asset: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default="TON",
    )

    # נכס ציטוט: למשל "USDT", "NIS"
    quote_asset: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default="USDT",
    )

    # רשת: ton_mainnet / ton_testnet / internal
    network: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="ton_testnet",
    )

    # מחיר ליחידה (quote per base)
    price: Mapped[Decimal] = mapped_column(
        Numeric(38, 10),
        nullable=False,
    )

    # כמות בסיסית כוללת
    amount: Mapped[Decimal] = mapped_column(
        Numeric(38, 10),
        nullable=False,
    )

    # כמות שבוצעה בפועל
    filled_amount: Mapped[Decimal] = mapped_column(
        Numeric(38, 10),
        nullable=False,
        default=Decimal("0"),
    )

    # סטטוס: open / partial / filled / cancelled
    status: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default="open",
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    def remaining_amount(self) -> Decimal:
        """כמה עוד נשאר לסחור בהזמנה הזו."""
        return self.amount - self.filled_amount

    def is_open(self) -> bool:
        return self.status == "open"

    def __repr__(self) -> str:
        return (
            f"<P2POrder id={self.id} owner={self.owner_telegram_id} "
            f"{self.side} {self.amount} {self.base_asset} @ {self.price} {self.quote_asset} "
            f"status={self.status}>"
        )
