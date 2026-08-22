from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ...core.rbac import require_permission
from ...database.session import get_db
from ..admin_auth.model import AdminUser
from .schema import AdminDashboardSummaryRead
from .service import AdminDashboardService

router = APIRouter(prefix="/api/admin/dashboard", tags=["admin-dashboard"])


@router.get("/summary", response_model=AdminDashboardSummaryRead)
def get_summary(
    db: Annotated[Session, Depends(get_db)],
    _admin: Annotated[AdminUser, Depends(require_permission("dashboard:read"))],
) -> AdminDashboardSummaryRead:
    return AdminDashboardService(db).summary()
