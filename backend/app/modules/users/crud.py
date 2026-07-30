from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from .model import User


class UserCrud:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_users(self, limit: int = 100) -> list[User]:
        statement = select(User).order_by(User.created_at.desc()).limit(limit)
        return list(self.db.scalars(statement).all())

    def get_by_id(self, user_id: str) -> User | None:
        return self.db.get(User, user_id)
