from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class PointTransactionRead(BaseModel):
    id: str
    user_id: str
    amount: int
    balance_after: int
    reason: str
    source: str
    admin_id: str | None = None
    conversion_id: str | None = None
    redeem_code_id: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
