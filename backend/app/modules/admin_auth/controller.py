from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ...core.rbac import get_current_admin
from ...database.session import get_db
from .model import AdminUser
from .schema import AdminAuthResponse, AdminLoginRequest, AdminProfile
from .service import AdminAuthService

router = APIRouter(prefix="/api/admin/auth", tags=["admin-auth"])


@router.post("/login", response_model=AdminAuthResponse)
def login(
    payload: AdminLoginRequest,
    db: Annotated[Session, Depends(get_db)],
) -> AdminAuthResponse:
    return AdminAuthService(db).login(payload.email, payload.password)


@router.get("/me", response_model=AdminProfile)
def me(
    admin: Annotated[AdminUser, Depends(get_current_admin)],
    db: Annotated[Session, Depends(get_db)],
) -> AdminProfile:
    return AdminAuthService(db).profile(admin)
