from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ...core.rbac import require_permission
from ...database.session import get_db
from ..admin_auth.model import AdminUser
from .schema import ConversionAdminRead
from .service import ConversionAdminService

router = APIRouter(prefix="/api/admin/conversions", tags=["admin-conversions"])


@router.get("", response_model=list[ConversionAdminRead])
def list_conversions(
    db: Annotated[Session, Depends(get_db)],
    _admin: Annotated[AdminUser, Depends(require_permission("conversions:read"))],
    limit: Annotated[int, Query(ge=1, le=300)] = 100,
) -> list[ConversionAdminRead]:
    return [ConversionAdminRead.model_validate(item) for item in ConversionAdminService(db).list_recent(limit)]
