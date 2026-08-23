from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from ...core.security import utc_now
from ...database.base import Base


class PointTransaction(Base):
    __tablename__ = "point_transactions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    amount: Mapped[int] = mapped_column(Integer)
    balance_after: Mapped[int] = mapped_column(Integer)
    reason: Mapped[str] = mapped_column(String(300))
    source: Mapped[str] = mapped_column(String(80), index=True)
    admin_id: Mapped[str | None] = mapped_column(String(36), default=None, index=True)
    conversion_id: Mapped[str | None] = mapped_column(String(36), default=None, index=True)
    redeem_code_id: Mapped[str | None] = mapped_column(String(36), default=None, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, index=True)
