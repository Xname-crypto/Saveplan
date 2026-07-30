from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class ConversionAdminRead(BaseModel):
    id: str
    user_id: str
    filename: str
    source_type: str
    subject: str
    status: str
    ocr_state: str | None = None
    points_charged: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
