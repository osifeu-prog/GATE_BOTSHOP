from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel


class UserOut(BaseModel):
    id: int
    telegram_id: int
    username: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]
    xp: int
    level: str
    membership_tier: str
    created_at: datetime

    class Config:
        from_attributes = True


class WalletOut(BaseModel):
    id: int
    user_id: int
    is_demo: bool
    balance_slh: float
    balance_usdt: float
    created_at: datetime

    class Config:
        from_attributes = True


class StakeOut(BaseModel):
    id: int
    user_id: int
    is_demo: bool
    amount_slh: float
    lock_days: int
    apy: float
    active: bool
    started_at: datetime
    ends_at: datetime
    last_yield_calculated_at: Optional[datetime]

    class Config:
        from_attributes = True


class ReferralSummary(BaseModel):
    direct_count: int
    level2_count: int
    level3_count: int
    total_downline: int


class AnalyticsEventOut(BaseModel):
    id: int
    event_type: str
    created_at: datetime

    class Config:
        from_attributes = True
