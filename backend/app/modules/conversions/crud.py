from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from .model import Conversion


class ConversionCrud:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_recent(self, limit: int = 100) -> list[Conversion]:
        statement = select(Conversion).order_by(Conversion.created_at.desc()).limit(limit)
        return list(self.db.scalars(statement).all())
