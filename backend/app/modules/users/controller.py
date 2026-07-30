from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ...core.rbac import require_permission
from ...database.session import get_db
from ..admin_auth.model import AdminUser
from .schema import PointAdjustRequest, UserAdminRead
from .service import UserAdminService

router = APIRouter(prefix="/api/admin/users", tags=["admin-users"])


@router.get("", response_model=list[UserAdminRead])
def list_users(
    db: Annotated[Session, Depends(get_db)],
    _admin: Annotated[AdminUser, Depends(require_permission("users:read"))],
    limit: Annotated[int, Query(ge=1, le=300)] = 100,
) -> list[UserAdminRead]:
    return [UserAdminRead.model_validate(item) for item in UserAdminService(db).list_users(limit)]


@router.patch("/{user_id}/points", response_model=UserAdminRead)
def adjust_points(
    user_id: str,
    payload: PointAdjustRequest,
    db: Annotated[Session, Depends(get_db)],
    admin: Annotated[AdminUser, Depends(require_permission("users:update_points"))],
) -> UserAdminRead:
    user = UserAdminService(db).adjust_points(
        admin_id=admin.id,
        user_id=user_id,
        amount=payload.amount,
        reason=payload.reason,
    )
    return UserAdminRead.model_validate(user)
