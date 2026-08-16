from __future__ import annotations

from pydantic import BaseModel, Field


class CreatePendingOrderRequest(BaseModel):
    plan_id: str = Field(min_length=3, max_length=60)
    contact_name: str = Field(min_length=2, max_length=80)
    contact_phone: str = Field(min_length=6, max_length=32)
    contact_email: str = Field(min_length=3, max_length=254)


class PendingOrderResponse(BaseModel):
    order_id: str
    status: str
    payment_url: str
