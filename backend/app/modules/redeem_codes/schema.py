from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from ..auth.schema import AuthUser


class RedeemCodeCreateRequest(BaseModel):
    batch_name: str = Field(min_length=2, max_length=120)
    count: int = Field(ge=1, le=500)
    points: int = Field(ge=1, le=100000)
    prefix: str | None = Field(default=None, max_length=24)
    expires_at: datetime | None = None
    note: str | None = Field(default=None, max_length=300)
    max_redemptions: int = Field(default=1, ge=1, le=1000)


class RedeemCodeRead(BaseModel):
    id: str
    code: str
    batch_name: str
    points: int
    max_redemptions: int
    redeemed_count: int
    is_active: bool
    expires_at: datetime | None = None
    note: str | None = None
    created_by_admin_id: str | None = None
    created_at: datetime
    updated_at: datetime
    status: str = ""

    model_config = {"from_attributes": True}


class RedeemCodeBatchResponse(BaseModel):
    batch_name: str
    codes: list[RedeemCodeRead]


class RedeemCodeClaimRequest(BaseModel):
    code: str = Field(min_length=3, max_length=48)


class RedeemCodeClaimResponse(BaseModel):
    message: str
    code: str
    points_earned: int
    balance_after: int
    user: AuthUser
