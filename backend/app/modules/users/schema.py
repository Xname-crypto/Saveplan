from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class UserAdminRead(BaseModel):
    id: str
    email: str
    username: str
    job: str | None = None
    point_balance: int
    avatar_name: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class PointAdjustRequest(BaseModel):
    amount: int = Field(ge=-100000, le=100000)
    reason: str = Field(min_length=2, max_length=300)
