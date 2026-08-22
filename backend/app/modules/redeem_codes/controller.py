from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ...core.rbac import require_permission
from ...database.session import get_db
from ..admin_auth.model import AdminUser
from .schema import RedeemCodeBatchResponse, RedeemCodeCreateRequest, RedeemCodeRead
from .service import RedeemCodeService

router = APIRouter(prefix="/api/admin/redeem-codes", tags=["admin-redeem-codes"])


def _to_read_model(service: RedeemCodeService, item) -> RedeemCodeRead:
    base = RedeemCodeRead.model_validate(item)
    return base.model_copy(update={"status": service.status_of(item)})


@router.get("", response_model=list[RedeemCodeRead])
def list_redeem_codes(
    db: Annotated[Session, Depends(get_db)],
    _admin: Annotated[AdminUser, Depends(require_permission("redeem_codes:read"))],
    limit: Annotated[int, Query(ge=1, le=300)] = 100,
) -> list[RedeemCodeRead]:
    service = RedeemCodeService(db)
    return [_to_read_model(service, item) for item in service.list_codes(limit)]


@router.post("", response_model=RedeemCodeBatchResponse)
def create_redeem_codes(
    payload: RedeemCodeCreateRequest,
    db: Annotated[Session, Depends(get_db)],
    admin: Annotated[AdminUser, Depends(require_permission("redeem_codes:manage"))],
) -> RedeemCodeBatchResponse:
    codes = RedeemCodeService(db).create_batch(admin_id=admin.id, payload=payload)
    return RedeemCodeBatchResponse(
        batch_name=payload.batch_name.strip(),
        codes=[_to_read_model(RedeemCodeService(db), item) for item in codes],
    )


@router.patch("/{code_id}/deactivate", response_model=RedeemCodeRead)
def deactivate_redeem_code(
    code_id: str,
    db: Annotated[Session, Depends(get_db)],
    admin: Annotated[AdminUser, Depends(require_permission("redeem_codes:manage"))],
) -> RedeemCodeRead:
    code = RedeemCodeService(db).deactivate(admin_id=admin.id, code_id=code_id)
    return _to_read_model(RedeemCodeService(db), code)
