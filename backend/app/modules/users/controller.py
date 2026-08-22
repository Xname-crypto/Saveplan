from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from fastapi import HTTPException, status

from ...core.rbac import require_permission
from ...database.session import get_db
from ..admin_auth.model import AdminUser
from .schema import (
    PointAdjustRequest,
    UserAdminCreateRequest,
    UserAdminRead,
    UserAdminUpdateRequest,
)
from .service import UserAdminService

router = APIRouter(prefix="/api/admin/users", tags=["admin-users"])


@router.get("", response_model=list[UserAdminRead])
def list_users(
    db: Annotated[Session, Depends(get_db)],
    _admin: Annotated[AdminUser, Depends(require_permission("users:read"))],
    limit: Annotated[int, Query(ge=1, le=300)] = 100,
    query: Annotated[str | None, Query(max_length=120)] = None,
) -> list[UserAdminRead]:
    return [UserAdminRead.model_validate(item) for item in UserAdminService(db).list_users(limit, query=query)]


@router.get("/{user_id}", response_model=UserAdminRead)
def get_user(
    user_id: str,
    db: Annotated[Session, Depends(get_db)],
    _admin: Annotated[AdminUser, Depends(require_permission("users:read"))],
) -> UserAdminRead:
    return UserAdminRead.model_validate(UserAdminService(db).get_user(user_id))


@router.post("", response_model=UserAdminRead, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserAdminCreateRequest,
    db: Annotated[Session, Depends(get_db)],
    admin: Annotated[AdminUser, Depends(require_permission("users:create"))],
) -> UserAdminRead:
    return UserAdminRead.model_validate(UserAdminService(db).create_user(admin_id=admin.id, payload=payload))


@router.patch("/{user_id}", response_model=UserAdminRead)
def update_user(
    user_id: str,
    payload: UserAdminUpdateRequest,
    db: Annotated[Session, Depends(get_db)],
    admin: Annotated[AdminUser, Depends(require_permission("users:update"))],
) -> UserAdminRead:
    return UserAdminRead.model_validate(
        UserAdminService(db).update_user(admin_id=admin.id, user_id=user_id, payload=payload)
    )


@router.delete("/{user_id}", response_model=UserAdminRead)
def delete_user(
    user_id: str,
    db: Annotated[Session, Depends(get_db)],
    admin: Annotated[AdminUser, Depends(require_permission("users:delete"))],
) -> UserAdminRead:
    return UserAdminRead.model_validate(UserAdminService(db).delete_user(admin_id=admin.id, user_id=user_id))


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
