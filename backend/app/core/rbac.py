from __future__ import annotations

from collections.abc import Callable
from typing import Annotated

from fastapi import Depends, Header, HTTPException, Request, status
from sqlalchemy.orm import Session

from ..config import ADMIN_JWT_SECRET, ADMIN_SESSION_COOKIE_NAME
from ..database.session import get_db
from ..modules.admin_auth.crud import AdminUserCrud
from ..modules.admin_auth.model import AdminUser
from ..modules.audit_logs.service import AuditLogService
from .security import verify_token


def get_current_admin(
    db: Annotated[Session, Depends(get_db)],
    request: Request,
    authorization: Annotated[str | None, Header()] = None,
) -> AdminUser:
    token = (
        authorization.removeprefix("Bearer ").strip()
        if authorization and authorization.startswith("Bearer ")
        else request.cookies.get(ADMIN_SESSION_COOKIE_NAME)
    )
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Please sign in as an administrator.",
        )

    payload = verify_token(token, ADMIN_JWT_SECRET)
    admin_id = payload.get("sub")
    token_type = payload.get("type")
    token_version = payload.get("token_version")

    if token_type != "admin" or not isinstance(admin_id, str) or not isinstance(token_version, int):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin login state.",
        )

    admin = AdminUserCrud(db).get_by_id(admin_id)
    if admin is None or not admin.is_active or admin.token_version != token_version:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin session expired. Please sign in again.",
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
                detail="Current administrator does not have permission for this action.",
            )
        return admin

    return dependency
