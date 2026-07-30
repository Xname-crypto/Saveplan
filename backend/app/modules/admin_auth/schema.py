from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class AdminLoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=1, max_length=128)


class AdminProfile(BaseModel):
    id: str
    email: str
    username: str
    is_active: bool
    roles: list[str]
    permissions: list[str]
    last_login_at: datetime | None = None
    created_at: datetime


class AdminAuthResponse(BaseModel):
    token: str
    admin: AdminProfile
