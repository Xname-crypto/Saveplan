from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class AuditLogRead(BaseModel):
    id: str
    admin_id: str | None
    action: str
    resource: str
    detail: dict
    created_at: datetime

    model_config = {"from_attributes": True}
