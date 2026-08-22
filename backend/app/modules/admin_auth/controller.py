from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from ...config import (
    ADMIN_SESSION_COOKIE_DOMAIN,
    ADMIN_SESSION_COOKIE_NAME,
    ADMIN_SESSION_COOKIE_SAMESITE,
    ADMIN_SESSION_COOKIE_SECURE,
    ADMIN_SESSION_MINUTES,
)
from ...core.rbac import get_current_admin
from ...database.session import get_db
from .model import AdminUser
from .schema import AdminAuthResponse, AdminLoginRequest, AdminProfile
from .service import AdminAuthService

router = APIRouter(prefix="/api/admin/auth", tags=["admin-auth"])


@router.post("/login", response_model=AdminAuthResponse)
def login(
    payload: AdminLoginRequest,
    response: Response,
    db: Annotated[Session, Depends(get_db)],
) -> AdminAuthResponse:
    auth = AdminAuthService(db).login(payload.email, payload.password)
    response.set_cookie(
        key=ADMIN_SESSION_COOKIE_NAME,
        value=auth.token,
        httponly=True,
        secure=ADMIN_SESSION_COOKIE_SECURE,
        samesite=ADMIN_SESSION_COOKIE_SAMESITE,
        domain=ADMIN_SESSION_COOKIE_DOMAIN,
        max_age=ADMIN_SESSION_MINUTES * 60,
        path="/",
    )
    return auth


@router.post("/logout")
def logout(response: Response) -> dict[str, str]:
    response.delete_cookie(
        key=ADMIN_SESSION_COOKIE_NAME,
        domain=ADMIN_SESSION_COOKIE_DOMAIN,
        path="/",
    )
    return {"message": "已退出登录"}


@router.get("/me", response_model=AdminProfile)
def me(
    admin: Annotated[AdminUser, Depends(get_current_admin)],
    db: Annotated[Session, Depends(get_db)],
) -> AdminProfile:
    return AdminAuthService(db).profile(admin)
