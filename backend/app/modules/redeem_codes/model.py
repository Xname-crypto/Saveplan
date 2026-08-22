from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from ...core.security import utc_now
from ...database.base import Base


class RedeemCode(Base):
    __tablename__ = "redeem_codes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    code: Mapped[str] = mapped_column(String(48), unique=True, index=True)
    batch_name: Mapped[str] = mapped_column(String(120), index=True)
    points: Mapped[int] = mapped_column(Integer)
    max_redemptions: Mapped[int] = mapped_column(Integer, default=1)
    redeemed_count: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    note: Mapped[str | None] = mapped_column(String(300), default=None)
    created_by_admin_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("admin_users.id", ondelete="SET NULL"),
        default=None,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)
