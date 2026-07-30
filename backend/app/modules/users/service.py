from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from ..audit_logs.service import AuditLogService
from ..points.service import PointService
from .crud import UserCrud
from .model import User


class UserAdminService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.crud = UserCrud(db)

    def list_users(self, limit: int = 100) -> list[User]:
        return self.crud.list_users(limit)

    def adjust_points(
        self,
        *,
        admin_id: str,
        user_id: str,
        amount: int,
        reason: str,
    ) -> User:
        user = self.crud.get_by_id(user_id)
        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在。")

        before = user.point_balance
        user.point_balance += amount
        PointService(self.db).record_adjustment(
            user_id=user.id,
            amount=amount,
            balance_after=user.point_balance,
            reason=reason,
            admin_id=admin_id,
        )
        AuditLogService(self.db).record(
            admin_id=admin_id,
            action="user_points_adjusted",
            resource=f"users:{user.id}",
            detail={
                "amount": amount,
                "balance_before": before,
                "balance_after": user.point_balance,
                "reason": reason,
            },
        )
        self.db.commit()
        self.db.refresh(user)
        return user
