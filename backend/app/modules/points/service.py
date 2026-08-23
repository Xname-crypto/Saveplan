from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from .crud import PointCrud
from .model import PointTransaction


class PointService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.crud = PointCrud(db)

    def record_adjustment(
        self,
        *,
        user_id: str,
        amount: int,
        balance_after: int,
        reason: str,
        admin_id: str,
    ) -> PointTransaction:
        return self.crud.create(
            PointTransaction(
                id=str(uuid.uuid4()),
                user_id=user_id,
                amount=amount,
                balance_after=balance_after,
                reason=reason,
                source="admin_adjustment",
                admin_id=admin_id,
            )
        )

    def record_conversion_charge(
        self,
        *,
        user_id: str,
        amount: int,
        balance_after: int,
        reason: str,
        conversion_id: str,
    ) -> PointTransaction:
        return self.crud.create(
            PointTransaction(
                id=str(uuid.uuid4()),
                user_id=user_id,
                amount=amount,
                balance_after=balance_after,
                reason=reason,
                source="conversion",
                conversion_id=conversion_id,
            )
        )

    def record_redeem_code(
        self,
        *,
        user_id: str,
        amount: int,
        balance_after: int,
        reason: str,
        redeem_code_id: str,
    ) -> PointTransaction:
        return self.crud.create(
            PointTransaction(
                id=str(uuid.uuid4()),
                user_id=user_id,
                amount=amount,
                balance_after=balance_after,
                reason=reason,
                source="redeem_code",
                redeem_code_id=redeem_code_id,
            )
        )
