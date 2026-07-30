from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from ...core.security import utc_now
from ...database.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    email: Mapped[str] = mapped_column(String(254), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(128))
    password_salt: Mapped[str] = mapped_column(String(64))
    username: Mapped[str] = mapped_column(String(80))
    job: Mapped[str | None] = mapped_column(String(120), default=None)
    bio: Mapped[str | None] = mapped_column(Text, default=None)
    interests: Mapped[list] = mapped_column(JSON, default=list)
    avatar_name: Mapped[str | None] = mapped_column(String(255), default=None)
    token_version: Mapped[int] = mapped_column(Integer, default=0)
    point_balance: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)
