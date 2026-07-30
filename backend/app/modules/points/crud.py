from __future__ import annotations

from sqlalchemy.orm import Session

from .model import PointTransaction


class PointCrud:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, transaction: PointTransaction) -> PointTransaction:
        self.db.add(transaction)
        self.db.flush()
        return transaction
