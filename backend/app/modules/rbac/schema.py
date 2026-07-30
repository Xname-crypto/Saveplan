from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class PermissionRead(BaseModel):
    id: str
    code: str
    name: str
    group: str
    description: str | None = None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class RoleRead(BaseModel):
    id: str
    code: str
    name: str
    description: str | None = None
    is_active: bool
    created_at: datetime
    permissions: list[PermissionRead] = []

    model_config = {"from_attributes": True}
