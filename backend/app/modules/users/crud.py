from __future__ import annotations

from sqlalchemy import delete, or_, select
from sqlalchemy.orm import Session

from .model import User


class UserCrud:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_users(self, limit: int = 100, query: str | None = None) -> list[User]:
        statement = select(User)
        if query:
            pattern = f"%{query.strip()}%"
            statement = statement.where(
                or_(
                    User.email.ilike(pattern),
                    User.username.ilike(pattern),
                    User.job.ilike(pattern),
                )
            )
        statement = statement.order_by(User.created_at.desc()).limit(limit)
        return list(self.db.scalars(statement).all())

    def get_by_id(self, user_id: str) -> User | None:
        return self.db.get(User, user_id)

    def get_by_email(self, email: str) -> User | None:
        statement = select(User).where(User.email == email)
        return self.db.scalar(statement)

    def create(self, user: User) -> User:
        self.db.add(user)
        self.db.flush()
        return user

    def delete(self, user: User) -> None:
        self.db.delete(user)
        self.db.flush()
