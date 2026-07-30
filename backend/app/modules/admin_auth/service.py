from __future__ import annotations

import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from ...config import (
    ADMIN_BOOTSTRAP_EMAIL,
    ADMIN_BOOTSTRAP_PASSWORD,
    ADMIN_BOOTSTRAP_USERNAME,
    ADMIN_JWT_SECRET,
    ADMIN_SESSION_MINUTES,
)
from ...core.rbac import admin_permissions
from ...core.security import create_token, hash_password, utc_now, verify_password
from ..audit_logs.service import AuditLogService
from ..rbac.service import RbacService
from .crud import AdminUserCrud
from .model import AdminUser
from .schema import AdminAuthResponse, AdminProfile


def normalize_email(email: str) -> str:
    normalized = email.strip().lower()
    if "@" not in normalized or "." not in normalized.rsplit("@", 1)[-1]:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="请输入有效的管理员邮箱。",
        )
    return normalized


class AdminAuthService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.crud = AdminUserCrud(db)

    def bootstrap_super_admin(self) -> None:
        RbacService(self.db).ensure_default_rbac()
        if self.crud.any_admin_exists():
            return
        if not ADMIN_BOOTSTRAP_EMAIL or not ADMIN_BOOTSTRAP_PASSWORD:
            return

        password_hash, password_salt = hash_password(ADMIN_BOOTSTRAP_PASSWORD)
        role = RbacService(self.db).ensure_default_rbac()
        admin = AdminUser(
            id=str(uuid.uuid4()),
            email=normalize_email(ADMIN_BOOTSTRAP_EMAIL),
            username=ADMIN_BOOTSTRAP_USERNAME,
            password_hash=password_hash,
            password_salt=password_salt,
            roles=[role],
        )
        self.crud.create(admin)
        AuditLogService(self.db).record(
            admin_id=admin.id,
            action="admin_bootstrap",
            resource="admin_users",
            detail={"email": admin.email},
        )
        self.db.commit()

    def login(self, email: str, password: str) -> AdminAuthResponse:
        admin = self.crud.get_by_email(normalize_email(email))
        if admin is None or not admin.is_active or not verify_password(
            password,
            admin.password_hash,
            admin.password_salt,
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="管理员邮箱或密码不正确。",
            )

        admin.last_login_at = utc_now()
        permissions = sorted(admin_permissions(admin))
        token = create_token(
            subject=admin.id,
            secret=ADMIN_JWT_SECRET,
            expires_minutes=ADMIN_SESSION_MINUTES,
            payload={
                "type": "admin",
                "token_version": admin.token_version,
            },
        )
        AuditLogService(self.db).record(
            admin_id=admin.id,
            action="admin_login",
            resource="admin_auth",
            detail={"email": admin.email},
        )
        self.db.commit()
        return AdminAuthResponse(token=token, admin=self.profile(admin, permissions))

    def profile(self, admin: AdminUser, permissions: list[str] | None = None) -> AdminProfile:
        return AdminProfile(
            id=admin.id,
            email=admin.email,
            username=admin.username,
            is_active=admin.is_active,
            roles=[role.code for role in admin.roles if role.is_active],
            permissions=permissions or sorted(admin_permissions(admin)),
            last_login_at=admin.last_login_at,
            created_at=admin.created_at,
        )


def bootstrap_admin_security() -> None:
    from ...database.session import SessionLocal

    db = SessionLocal()
    try:
        AdminAuthService(db).bootstrap_super_admin()
    finally:
        db.close()
