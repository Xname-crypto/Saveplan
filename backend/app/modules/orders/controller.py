from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from ...database.session import get_db
from ..auth.schema import AuthUser
from ..auth.service import get_current_user
from .schema import CreatePendingOrderRequest, PendingOrderResponse
from .service import OrderService

router = APIRouter(prefix="/api/orders", tags=["orders"])


@router.post("/pending", response_model=PendingOrderResponse, status_code=status.HTTP_201_CREATED)
def create_pending_order(
    payload: CreatePendingOrderRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[AuthUser, Depends(get_current_user)],
) -> PendingOrderResponse:
    return OrderService(db).create_pending_order(payload=payload, current_user=current_user)
