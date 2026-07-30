from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ...core.rbac import require_permission
from ...database.session import get_db
from ..admin_auth.model import AdminUser
from .schema import AuditLogRead
from .service import AuditLogService

router = APIRouter(prefix="/api/admin/audit-logs", tags=["admin-audit-logs"])


@router.get("", response_model=list[AuditLogRead])
def list_audit_logs(
    db: Annotated[Session, Depends(get_db)],
    _admin: Annotated[AdminUser, Depends(require_permission("audit_logs:read"))],
    limit: Annotated[int, Query(ge=1, le=300)] = 100,
) -> list[AuditLogRead]:
    return [AuditLogRead.model_validate(item) for item in AuditLogService(db).list_recent(limit)]
