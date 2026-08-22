from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class BroadcastCreateRequest(BaseModel):
    channel: Literal["announcement", "popup"]
    scope: Literal["global", "user"] = "global"
    target_user_id: str | None = None
    title: str = Field(min_length=2, max_length=120)
    content: str = Field(min_length=2, max_length=4000)
    priority: int = Field(default=0, ge=0, le=100)
    starts_at: datetime | None = None
    ends_at: datetime | None = None

    @model_validator(mode="after")
    def validate_target(self) -> "BroadcastCreateRequest":
        if self.channel == "announcement" and self.scope != "global":
            raise ValueError("announcement broadcasts must use global scope")
        if self.scope == "user" and self.channel != "popup":
            raise ValueError("user-scoped broadcasts must use popup channel")
        if self.scope == "user" and not self.target_user_id:
            raise ValueError("target_user_id is required when scope is user")
        if self.scope == "global":
            self.target_user_id = None
        return self


class BroadcastToggleRequest(BaseModel):
    is_active: bool


class BroadcastRead(BaseModel):
    id: str
    channel: str
    scope: str
    target_user_id: str | None = None
    title: str
    content: str
    priority: int
    is_active: bool
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    created_by_admin_id: str | None = None
    created_at: datetime
    updated_at: datetime
    status: str = ""

    model_config = {"from_attributes": True}
