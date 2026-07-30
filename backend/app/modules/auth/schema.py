from __future__ import annotations

from pydantic import BaseModel, Field


class AuthUser(BaseModel):
    id: str
    email: str
    username: str
    job: str | None = None
    bio: str | None = None
    interests: list[str] = Field(default_factory=list)
    avatar_name: str | None = None
    points: int = 0
    credits: int = 0
    created_at: str


class AuthResponse(BaseModel):
    token: str
    user: AuthUser


class RegisterRequest(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=6, max_length=128)
    username: str = Field(min_length=3, max_length=80)
    job: str = Field(min_length=1, max_length=120)
    bio: str | None = Field(default=None, max_length=600)
    interests: list[str] = Field(default_factory=list, max_length=12)
    avatar_name: str | None = Field(default=None, max_length=255)


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=1, max_length=128)


class ForgotPasswordRequest(BaseModel):
    email: str = Field(min_length=3, max_length=254)


class ForgotPasswordResponse(BaseModel):
    message: str
    reset_token: str | None = None
    reset_url: str | None = None


class ResetPasswordRequest(BaseModel):
    token: str = Field(min_length=16)
    password: str = Field(min_length=6, max_length=128)
