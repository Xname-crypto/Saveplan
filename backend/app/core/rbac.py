from __future__ import annotations

from collections.abc import Callable
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from ..config import ADMIN_JWT_SECRET
from ..database.session import get_db
from ..modules.admin_auth.crud import AdminUserCrud
from ..modules.admin_auth.model import AdminUser
from ..modules.audit_logs.service import AuditLogService
from .security import verify_token


def get_current_admin(
    db: Annotated[Session, Depends(get_db)],
    authorization: Annotated[str | None, Header()] = None,
) -> AdminUser:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="请先登录管理员后台。",
        )

    token = authorization.removeprefix("Bearer ").strip()
    payload = verify_token(token, ADMIN_JWT_SECRET)
    admin_id = payload.get("sub")
    token_type = payload.get("type")
    token_version = payload.get("token_version")

    if token_type != "admin" or not isinstance(admin_id, str) or not isinstance(token_version, int):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="管理员登录状态无效。",
        )

    admin = AdminUserCrud(db).get_by_id(admin_id)
    if admin is None or not admin.is_active or admin.token_version != token_version:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="管理员登录状态已失效。",
        )
    return admin


def admin_permissions(admin: AdminUser) -> set[str]:
    permissions: set[str] = set()
    for role in admin.roles:
        if not role.is_active:
            continue
        for permission in role.permissions:
            if permission.is_active:
                permissions.add(permission.code)
    return permissions


def require_permission(permission_code: str) -> Callable[..., AdminUser]:
    def dependency(
        db: Annotated[Session, Depends(get_db)],
        admin: Annotated[AdminUser, Depends(get_current_admin)],
    ) -> AdminUser:
        if permission_code not in admin_permissions(admin):
            AuditLogService(db).record(
                admin_id=admin.id,
                action="permission_denied",
                resource=permission_code,
                detail={"permission": permission_code},
            )
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="当前管理员没有该操作权限。",
            )
        return admin

    return dependency
