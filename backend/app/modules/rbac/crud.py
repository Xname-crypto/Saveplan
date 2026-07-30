from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from .model import Permission, Role


class RbacCrud:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_permission_by_code(self, code: str) -> Permission | None:
        return self.db.scalar(select(Permission).where(Permission.code == code))

    def get_role_by_code(self, code: str) -> Role | None:
        return self.db.scalar(select(Role).where(Role.code == code))

    def list_permissions(self) -> list[Permission]:
        return list(self.db.scalars(select(Permission).order_by(Permission.group, Permission.code)).all())

    def list_roles(self) -> list[Role]:
        return list(self.db.scalars(select(Role).order_by(Role.code)).unique().all())

    def create_permission(self, permission: Permission) -> Permission:
        self.db.add(permission)
        self.db.flush()
        return permission

    def create_role(self, role: Role) -> Role:
        self.db.add(role)
        self.db.flush()
        return role
