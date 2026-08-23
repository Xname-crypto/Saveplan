from __future__ import annotations

import secrets
import string
import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..audit_logs.service import AuditLogService
from ..points.model import PointTransaction
from ..points.service import PointService
from ..users.model import User
from .model import RedeemCode
from .schema import RedeemCodeCreateRequest


def _as_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _normalize_prefix(prefix: str | None, fallback: str) -> str:
    raw = (prefix or fallback or "SAVEPLAN").strip().upper()
    cleaned = [char for char in raw if char in string.ascii_uppercase + string.digits]
    value = "".join(cleaned)[:12]
    return value or "SAVEPLAN"


def _code_status(code: RedeemCode) -> str:
    if not code.is_active:
        return "inactive"
    if code.expires_at and _as_utc(code.expires_at) < datetime.now(timezone.utc):
        return "expired"
    if code.redeemed_count >= code.max_redemptions:
        return "used"
    return "active"


def _normalize_code(value: str) -> str:
    return "".join(ch for ch in value.strip().upper() if ch.isalnum() or ch == "-")


class RedeemCodeService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_codes(self, limit: int = 100) -> list[RedeemCode]:
        statement = select(RedeemCode).order_by(RedeemCode.created_at.desc()).limit(limit)
        return list(self.db.scalars(statement).all())

    def create_batch(self, *, admin_id: str, payload: RedeemCodeCreateRequest) -> list[RedeemCode]:
        batch_name = payload.batch_name.strip()
        prefix = _normalize_prefix(payload.prefix, batch_name)
        custom_code = _normalize_code(payload.custom_code) if payload.custom_code else None
        expires_at = _as_utc(payload.expires_at)
        created: list[RedeemCode] = []
        reserved_codes: set[str] = set()
        if custom_code:
            if payload.count != 1:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="指定兑换码时数量只能为 1。",
                )
            if len(custom_code) < 3:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="兑换码至少需要 3 个字符。",
                )
            exists = self.db.scalar(select(RedeemCode.id).where(RedeemCode.code == custom_code))
            if exists is not None:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="兑换码已存在，请重新生成。")
            generated_values = [custom_code]
        else:
            generated_values = []

        for _index in range(payload.count):
            for _attempt in range(20):
                generated = generated_values[_index] if custom_code else f"{prefix}-{secrets.token_hex(3).upper()}"
                if generated in reserved_codes:
                    continue
                exists = self.db.scalar(select(RedeemCode.id).where(RedeemCode.code == generated))
                if exists is not None:
                    continue
                reserved_codes.add(generated)
                code = RedeemCode(
                    id=str(uuid.uuid4()),
                    code=generated,
                    batch_name=batch_name,
                    points=payload.points,
                    max_redemptions=payload.max_redemptions,
                    redeemed_count=0,
                    is_active=True,
                    expires_at=expires_at,
                    note=payload.note.strip() if payload.note else None,
                    created_by_admin_id=admin_id,
                )
                self.db.add(code)
                created.append(code)
                break
            else:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="生成兑换码时发生冲突，请重试。",
                )

        self.db.flush()
        AuditLogService(self.db).record(
            admin_id=admin_id,
            action="redeem_codes_created",
            resource=f"redeem_codes:{batch_name}",
            detail={
                "batch_name": batch_name,
                "count": len(created),
                "points": payload.points,
                "max_redemptions": payload.max_redemptions,
                "expires_at": expires_at.isoformat() if expires_at else None,
            },
        )
        self.db.commit()
        for item in created:
            self.db.refresh(item)
        return created

    def deactivate(self, *, admin_id: str, code_id: str) -> RedeemCode:
        code = self.db.get(RedeemCode, code_id)
        if code is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="兑换码不存在。")

        code.is_active = False
        AuditLogService(self.db).record(
            admin_id=admin_id,
            action="redeem_code_deactivated",
            resource=f"redeem_codes:{code.code}",
            detail={"code": code.code},
        )
        self.db.commit()
        self.db.refresh(code)
        return code

    def claim(self, *, user_id: str, code_value: str) -> tuple[RedeemCode, User]:
        normalized_code = _normalize_code(code_value)
        if not normalized_code:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="请输入兑换码。")

        code = self.db.scalar(select(RedeemCode).where(RedeemCode.code == normalized_code))
        if code is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="兑换码不存在。")

        status_value = _code_status(code)
        if status_value == "inactive":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="兑换码已停用。")
        if status_value == "expired":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="兑换码已过期。")
        if status_value == "used":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="兑换码已被领取完。")

        user = self.db.get(User, user_id)
        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在。")

        already_claimed = self.db.scalar(
            select(PointTransaction.id).where(
                PointTransaction.user_id == user_id,
                PointTransaction.redeem_code_id == code.id,
            )
        )
        if already_claimed is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="你已经领取过这个兑换码了。")

        user.point_balance = (user.point_balance or 0) + code.points
        code.redeemed_count += 1
        PointService(self.db).record_redeem_code(
            user_id=user.id,
            amount=code.points,
            balance_after=user.point_balance,
            reason=f"兑换码 {code.code} 领取积分",
            redeem_code_id=code.id,
        )
        self.db.commit()
        self.db.refresh(code)
        self.db.refresh(user)
        return code, user

    @staticmethod
    def status_of(code: RedeemCode) -> str:
        return _code_status(code)
