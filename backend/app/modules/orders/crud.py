from __future__ import annotations

from sqlalchemy.orm import Session

from .model import Order


class OrderCrud:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, order: Order) -> Order:
        self.db.add(order)
        self.db.flush()
        return order
