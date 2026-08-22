from __future__ import annotations

import uuid

from fastapi import HTTPException, status
from sqlalchemy import delete, update
from sqlalchemy.orm import Session

from ...config import INITIAL_USER_POINTS
from ...core.security import hash_password
from ..audit_logs.service import AuditLogService
from ..points.service import PointService
from ..auth.model import PasswordReset
from ..broadcasts.model import BroadcastMessage
from ..conversions.model import Conversion
from ..orders.model import Order
from ..points.model import PointTransaction
from .crud import UserCrud
from .model import User
from .schema import UserAdminCreateRequest, UserAdminUpdateRequest


def normalize_email(email: str) -> str:
    normalized = email.strip().lower()
    if "@" not in normalized or "." not in normalized.rsplit("@", 1)[-1]:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="请输入有效的邮箱地址。")
    return normalized


def _clean_optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    text = value.strip()
    return text or None


def _clean_interests(values: list[str] | None) -> list[str]:
    if not values:
        return []
    return [item.strip() for item in values if isinstance(item, str) and item.strip()]


class UserAdminService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.crud = UserCrud(db)

    def list_users(self, limit: int = 100, query: str | None = None) -> list[User]:
        return self.crud.list_users(limit, query=query)

    def get_user(self, user_id: str) -> User:
        user = self.crud.get_by_id(user_id)
        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在。")
        return user

    def create_user(self, *, admin_id: str, payload: UserAdminCreateRequest) -> User:
        email = normalize_email(payload.email)
        if self.crud.get_by_email(email) is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="这个邮箱已经存在。")

        password_hash, password_salt = hash_password(payload.password)
        point_balance = payload.point_balance if payload.point_balance is not None else INITIAL_USER_POINTS
        user = self.crud.create(
            User(
                id=str(uuid.uuid4()),
                email=email,
                password_hash=password_hash,
                password_salt=password_salt,
                username=payload.username.strip(),
                job=_clean_optional_text(payload.job),
                bio=_clean_optional_text(payload.bio),
                interests=_clean_interests(payload.interests),
                avatar_name=_clean_optional_text(payload.avatar_name),
                point_balance=point_balance,
            )
        )
        if point_balance:
            PointService(self.db).record_adjustment(
                user_id=user.id,
                amount=point_balance,
                balance_after=point_balance,
                reason="管理员创建用户初始积分",
                admin_id=admin_id,
            )
        AuditLogService(self.db).record(
            admin_id=admin_id,
            action="user_created",
            resource=f"users:{user.id}",
            detail={
                "email": user.email,
                "username": user.username,
                "job": user.job,
                "point_balance": user.point_balance,
            },
        )
        self.db.commit()
        self.db.refresh(user)
        return user

    def update_user(
        self,
        *,
        admin_id: str,
        user_id: str,
        payload: UserAdminUpdateRequest,
    ) -> User:
        user = self.get_user(user_id)
        before = {
            "email": user.email,
            "username": user.username,
            "job": user.job,
            "bio": user.bio,
            "interests": list(user.interests) if isinstance(user.interests, list) else [],
            "avatar_name": user.avatar_name,
        }

        if payload.email is not None:
            email = normalize_email(payload.email)
            existing = self.crud.get_by_email(email)
            if existing is not None and existing.id != user.id:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="这个邮箱已经存在。")
            user.email = email
        if payload.username is not None:
            user.username = payload.username.strip()
        if payload.job is not None:
            user.job = _clean_optional_text(payload.job)
        if payload.bio is not None:
            user.bio = _clean_optional_text(payload.bio)
        if payload.interests is not None:
            user.interests = _clean_interests(payload.interests)
        if payload.avatar_name is not None:
            user.avatar_name = _clean_optional_text(payload.avatar_name)

        AuditLogService(self.db).record(
            admin_id=admin_id,
            action="user_updated",
            resource=f"users:{user.id}",
            detail={
                "before": before,
                "after": {
                    "email": user.email,
                    "username": user.username,
                    "job": user.job,
                    "bio": user.bio,
                    "interests": list(user.interests) if isinstance(user.interests, list) else [],
                    "avatar_name": user.avatar_name,
                },
            },
        )
        self.db.commit()
        self.db.refresh(user)
        return user

    def delete_user(self, *, admin_id: str, user_id: str) -> User:
        user = self.get_user(user_id)
        snapshot = User(
            id=user.id,
            email=user.email,
            password_hash=user.password_hash,
            password_salt=user.password_salt,
            username=user.username,
            job=user.job,
            bio=user.bio,
            interests=list(user.interests) if isinstance(user.interests, list) else [],
            avatar_name=user.avatar_name,
            token_version=user.token_version,
            point_balance=user.point_balance,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )
        self.db.execute(delete(PasswordReset).where(PasswordReset.user_id == user.id))
        self.db.execute(delete(PointTransaction).where(PointTransaction.user_id == user.id))
        self.db.execute(delete(Order).where(Order.user_id == user.id))
        self.db.execute(delete(Conversion).where(Conversion.user_id == user.id))
        self.db.execute(
            update(BroadcastMessage)
            .where(BroadcastMessage.target_user_id == user.id)
            .values(target_user_id=None)
        )
        self.crud.delete(user)
        AuditLogService(self.db).record(
            admin_id=admin_id,
            action="user_deleted",
            resource=f"users:{user.id}",
            detail={"email": snapshot.email, "username": snapshot.username},
        )
        self.db.commit()
        return snapshot

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
