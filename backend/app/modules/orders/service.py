from __future__ import annotations

import re
import uuid
from dataclasses import dataclass
from urllib.parse import urlparse

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from ...config import ZPAY_PAYMENT_URL_TEMPLATE
from ..auth.schema import AuthUser
from ..auth.service import normalize_email
from .crud import OrderCrud
from .model import Order
from .schema import CreatePendingOrderRequest, PendingOrderResponse


@dataclass(frozen=True)
class PaidPlan:
    id: str
    name: str
    billing_period: str
    amount_fen: int


PAID_PLANS = {
    "rescue-monthly": PaidPlan(
        id="rescue-monthly",
        name="高效抢救",
        billing_period="monthly",
        amount_fen=2900,
    ),
    "elite-yearly": PaidPlan(
        id="elite-yearly",
        name="学术精英",
        billing_period="yearly",
        amount_fen=19900,
    ),
}


class OrderService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.crud = OrderCrud(db)

    def create_pending_order(
        self,
        *,
        payload: CreatePendingOrderRequest,
        current_user: AuthUser,
    ) -> PendingOrderResponse:
        plan = PAID_PLANS.get(payload.plan_id)
        if plan is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="请选择有效的付费套餐。",
            )

        contact_name = payload.contact_name.strip()
        contact_phone = payload.contact_phone.strip()
        contact_email = normalize_email(payload.contact_email)

        if len(contact_name) < 2:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="请填写有效的姓名。",
            )

        if not re.fullmatch(r"1\d{10}", contact_phone):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="请输入有效的 11 位手机号。",
            )

        order_id = str(uuid.uuid4())
        payment_url = self._build_payment_url(order_id=order_id, plan=plan)
        order = self.crud.create(
            Order(
                id=order_id,
                user_id=current_user.id,
                plan_id=plan.id,
                plan_name=plan.name,
                billing_period=plan.billing_period,
                amount_fen=plan.amount_fen,
                currency="CNY",
                contact_name=contact_name,
                contact_phone=contact_phone,
                contact_email=contact_email,
                status="pending_payment",
            )
        )
        self.db.commit()
        self.db.refresh(order)

        return PendingOrderResponse(
            order_id=order.id,
            status=order.status,
            payment_url=payment_url,
        )

    def _build_payment_url(self, *, order_id: str, plan: PaidPlan) -> str:
        if not ZPAY_PAYMENT_URL_TEMPLATE:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=(
                    "Z-Pay 尚未配置。请设置 ZPAY_PAYMENT_URL_TEMPLATE，"
                    "并使用 {order_id}、{amount_fen}、{plan_id} 占位符。"
                ),
            )

        payment_url = (
            ZPAY_PAYMENT_URL_TEMPLATE.replace("{order_id}", order_id)
            .replace("{amount_fen}", str(plan.amount_fen))
            .replace("{plan_id}", plan.id)
        )
        parsed = urlparse(payment_url)

        if parsed.scheme not in {"https", "http"} or not parsed.netloc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Z-Pay 支付地址配置无效。",
            )

        return payment_url
