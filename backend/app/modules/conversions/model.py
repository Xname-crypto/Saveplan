from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from ...core.security import utc_now
from ...database.base import Base


class Conversion(Base):
    __tablename__ = "conversions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    filename: Mapped[str] = mapped_column(String(255))
    stored_path: Mapped[str | None] = mapped_column(Text, default=None)
    source_type: Mapped[str] = mapped_column(String(40), index=True)
    subject: Mapped[str] = mapped_column(String(40), default="general")
    raw_text: Mapped[str] = mapped_column(Text, default="")
    text_state: Mapped[str] = mapped_column(String(40), default="text")
    status: Mapped[str] = mapped_column(String(40), index=True)
    questions_json: Mapped[list] = mapped_column(JSON, default=list)
    issues_json: Mapped[list] = mapped_column(JSON, default=list)
    assets_json: Mapped[list] = mapped_column(JSON, default=list)
    export_text: Mapped[str | None] = mapped_column(Text, default=None)
    ocr_provider: Mapped[str | None] = mapped_column(String(80), default=None)
    ocr_provider_job_id: Mapped[str | None] = mapped_column(String(160), default=None, index=True)
    ocr_state: Mapped[str | None] = mapped_column(String(40), default=None, index=True)
    ocr_total_pages: Mapped[int] = mapped_column(Integer, default=0)
    ocr_extracted_pages: Mapped[int] = mapped_column(Integer, default=0)
    ocr_result_url: Mapped[str | None] = mapped_column(Text, default=None)
    ocr_error: Mapped[str | None] = mapped_column(Text, default=None)
    points_charged: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)
