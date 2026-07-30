from __future__ import annotations

from sqlalchemy.orm import Session

from .crud import ConversionCrud
from .model import Conversion


class ConversionAdminService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.crud = ConversionCrud(db)

    def list_recent(self, limit: int = 100) -> list[Conversion]:
        return self.crud.list_recent(limit)
