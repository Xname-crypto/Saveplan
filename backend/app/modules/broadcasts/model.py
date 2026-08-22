from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from ...core.security import utc_now
from ...database.base import Base


class BroadcastMessage(Base):
    __tablename__ = "broadcast_messages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    channel: Mapped[str] = mapped_column(String(24), index=True)
    scope: Mapped[str] = mapped_column(String(24), index=True, default="global")
    target_user_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        default=None,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(120))
    content: Mapped[str] = mapped_column(Text)
    priority: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    starts_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    created_by_admin_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("admin_users.id", ondelete="SET NULL"),
        default=None,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)
