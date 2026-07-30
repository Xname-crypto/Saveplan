from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ...core.rbac import require_permission
from ...database.session import get_db
from ..admin_auth.model import AdminUser
from .schema import PermissionRead, RoleRead
from .service import RbacService

router = APIRouter(prefix="/api/admin/rbac", tags=["admin-rbac"])


@router.get("/permissions", response_model=list[PermissionRead])
def list_permissions(
    db: Annotated[Session, Depends(get_db)],
    _admin: Annotated[AdminUser, Depends(require_permission("rbac:read"))],
) -> list[PermissionRead]:
    return [PermissionRead.model_validate(item) for item in RbacService(db).list_permissions()]


@router.get("/roles", response_model=list[RoleRead])
def list_roles(
    db: Annotated[Session, Depends(get_db)],
    _admin: Annotated[AdminUser, Depends(require_permission("rbac:read"))],
) -> list[RoleRead]:
    return [RoleRead.model_validate(item) for item in RbacService(db).list_roles()]
