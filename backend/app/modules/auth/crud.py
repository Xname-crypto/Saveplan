from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from ..users.model import User
from .model import PasswordReset


class AuthCrud:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_user_by_id(self, user_id: str) -> User | None:
        return self.db.get(User, user_id)

    def get_user_by_email(self, email: str) -> User | None:
        return self.db.scalar(select(User).where(User.email == email))

    def create_user(self, user: User) -> User:
        self.db.add(user)
        self.db.flush()
        return user

    def delete_password_resets_for_user(self, user_id: str) -> None:
        self.db.execute(delete(PasswordReset).where(PasswordReset.user_id == user_id))

    def create_password_reset(self, reset: PasswordReset) -> PasswordReset:
        self.db.add(reset)
        self.db.flush()
        return reset

    def get_password_reset(self, token: str) -> PasswordReset | None:
        return self.db.get(PasswordReset, token)

    def delete_password_reset(self, token: str) -> None:
        self.db.execute(delete(PasswordReset).where(PasswordReset.token == token))
