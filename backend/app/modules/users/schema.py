from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class UserAdminRead(BaseModel):
    id: str
    email: str
    username: str
    job: str | None = None
    bio: str | None = None
    interests: list[str] = Field(default_factory=list)
    point_balance: int
    avatar_name: str | None = None
    created_at: datetime
    updated_at: datetime
    token_version: int = 0

    model_config = {"from_attributes": True}


class UserAdminCreateRequest(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=8, max_length=128)
    username: str = Field(min_length=3, max_length=80)
    job: str | None = Field(default=None, max_length=120)
    bio: str | None = Field(default=None, max_length=600)
    interests: list[str] = Field(default_factory=list, max_length=12)
    avatar_name: str | None = Field(default=None, max_length=255)
    point_balance: int | None = Field(default=None, ge=0, le=100000)


class UserAdminUpdateRequest(BaseModel):
    email: str | None = Field(default=None, min_length=3, max_length=254)
    username: str | None = Field(default=None, min_length=3, max_length=80)
    job: str | None = Field(default=None, max_length=120)
    bio: str | None = Field(default=None, max_length=600)
    interests: list[str] | None = Field(default=None, max_length=12)
    avatar_name: str | None = Field(default=None, max_length=255)


class PointAdjustRequest(BaseModel):
    amount: int = Field(ge=-100000, le=100000)
    reason: str = Field(min_length=2, max_length=300)
