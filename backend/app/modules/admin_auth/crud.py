from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from .model import AdminUser


class AdminUserCrud:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, admin_id: str) -> AdminUser | None:
        return self.db.get(AdminUser, admin_id)

    def get_by_email(self, email: str) -> AdminUser | None:
        return self.db.scalar(select(AdminUser).where(AdminUser.email == email))

    def any_admin_exists(self) -> bool:
        return self.db.scalar(select(AdminUser.id).limit(1)) is not None

    def create(self, admin: AdminUser) -> AdminUser:
        self.db.add(admin)
        self.db.flush()
        return admin
