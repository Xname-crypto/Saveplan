from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ...core.rbac import require_permission
from ...database.session import get_db
from ..admin_auth.model import AdminUser
from ..auth.service import get_current_user
from ..auth.schema import AuthUser
from .schema import BroadcastCreateRequest, BroadcastRead, BroadcastToggleRequest
from .service import BroadcastService

router = APIRouter(prefix="/api/admin/broadcasts", tags=["admin-broadcasts"])
public_router = APIRouter(prefix="/api/broadcasts", tags=["broadcasts"])


def _to_read_model(service: BroadcastService, message) -> BroadcastRead:
    base = BroadcastRead.model_validate(message)
    return base.model_copy(update={"status": service.status_of(message)})


@router.get("", response_model=list[BroadcastRead])
def list_broadcasts(
    db: Annotated[Session, Depends(get_db)],
    _admin: Annotated[AdminUser, Depends(require_permission("broadcasts:read"))],
    limit: Annotated[int, Query(ge=1, le=300)] = 100,
    channel: Annotated[str | None, Query()] = None,
    scope: Annotated[str | None, Query()] = None,
) -> list[BroadcastRead]:
    service = BroadcastService(db)
    return [
        _to_read_model(service, message)
        for message in service.list_messages(limit, channel=channel, scope=scope)
    ]


@router.post("", response_model=BroadcastRead)
def create_broadcast(
    payload: BroadcastCreateRequest,
    db: Annotated[Session, Depends(get_db)],
    admin: Annotated[AdminUser, Depends(require_permission("broadcasts:manage"))],
) -> BroadcastRead:
    service = BroadcastService(db)
    message = service.create_message(admin_id=admin.id, payload=payload)
    return _to_read_model(service, message)


@router.patch("/{message_id}", response_model=BroadcastRead)
def toggle_broadcast(
    message_id: str,
    payload: BroadcastToggleRequest,
    db: Annotated[Session, Depends(get_db)],
    admin: Annotated[AdminUser, Depends(require_permission("broadcasts:manage"))],
) -> BroadcastRead:
    service = BroadcastService(db)
    message = service.update_active(admin_id=admin.id, message_id=message_id, payload=payload)
    return _to_read_model(service, message)


@public_router.get("/active", response_model=list[BroadcastRead])
def list_active_broadcasts(db: Annotated[Session, Depends(get_db)]) -> list[BroadcastRead]:
    service = BroadcastService(db)
    return [_to_read_model(service, message) for message in service.list_active_messages()]


@public_router.get("/me", response_model=list[BroadcastRead])
def list_my_messages(
    current_user: Annotated[AuthUser, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[BroadcastRead]:
    service = BroadcastService(db)
    return [_to_read_model(service, message) for message in service.list_user_messages(current_user.id)]
