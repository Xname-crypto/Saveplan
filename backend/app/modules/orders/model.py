from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from ...core.security import utc_now
from ...database.base import Base


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    plan_id: Mapped[str] = mapped_column(String(60), index=True)
    plan_name: Mapped[str] = mapped_column(String(120))
    billing_period: Mapped[str] = mapped_column(String(20))
    amount_fen: Mapped[int] = mapped_column(Integer)
    currency: Mapped[str] = mapped_column(String(8), default="CNY")
    contact_name: Mapped[str] = mapped_column(String(80))
    contact_phone: Mapped[str] = mapped_column(String(32))
    contact_email: Mapped[str] = mapped_column(String(254))
    status: Mapped[str] = mapped_column(String(32), default="pending_payment", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)
