from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..audit_logs.service import AuditLogService
from ..users.model import User
from .model import BroadcastMessage
from .schema import BroadcastCreateRequest, BroadcastToggleRequest


def _as_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _broadcast_status(message: BroadcastMessage) -> str:
    now = datetime.now(timezone.utc)
    if not message.is_active:
        return "inactive"
    if message.starts_at and _as_utc(message.starts_at) > now:
        return "scheduled"
    if message.ends_at and _as_utc(message.ends_at) < now:
        return "expired"
    return "active"


class BroadcastService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_messages(
        self,
        limit: int = 100,
        *,
        channel: str | None = None,
        scope: str | None = None,
    ) -> list[BroadcastMessage]:
        statement = select(BroadcastMessage)
        if channel:
            statement = statement.where(BroadcastMessage.channel == channel)
        if scope:
            statement = statement.where(BroadcastMessage.scope == scope)
        statement = statement.order_by(BroadcastMessage.created_at.desc()).limit(limit)
        return list(self.db.scalars(statement).all())

    def list_active_messages(self) -> list[BroadcastMessage]:
        now = datetime.now(timezone.utc)
        statement = (
            select(BroadcastMessage)
            .where(BroadcastMessage.is_active.is_(True))
            .where((BroadcastMessage.starts_at.is_(None)) | (BroadcastMessage.starts_at <= now))
            .where((BroadcastMessage.ends_at.is_(None)) | (BroadcastMessage.ends_at >= now))
            .where(BroadcastMessage.scope == "global")
            .order_by(BroadcastMessage.priority.desc(), BroadcastMessage.created_at.desc())
        )
        return list(self.db.scalars(statement).all())

    def list_user_messages(self, user_id: str) -> list[BroadcastMessage]:
        now = datetime.now(timezone.utc)
        statement = (
            select(BroadcastMessage)
            .where(BroadcastMessage.is_active.is_(True))
            .where((BroadcastMessage.starts_at.is_(None)) | (BroadcastMessage.starts_at <= now))
            .where((BroadcastMessage.ends_at.is_(None)) | (BroadcastMessage.ends_at >= now))
            .where(
                (BroadcastMessage.scope == "user")
                & (BroadcastMessage.target_user_id == user_id)
            )
            .order_by(BroadcastMessage.priority.desc(), BroadcastMessage.created_at.desc())
        )
        return list(self.db.scalars(statement).all())

    def create_message(self, *, admin_id: str, payload: BroadcastCreateRequest) -> BroadcastMessage:
        if payload.scope == "user":
            target = self.db.get(User, payload.target_user_id) if payload.target_user_id else None
            if target is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="目标用户不存在。")

        message = BroadcastMessage(
            id=str(uuid.uuid4()),
            channel=payload.channel,
            scope=payload.scope,
            target_user_id=payload.target_user_id if payload.scope == "user" else None,
            title=payload.title.strip(),
            content=payload.content.strip(),
            priority=payload.priority,
            is_active=True,
            starts_at=_as_utc(payload.starts_at),
            ends_at=_as_utc(payload.ends_at),
            created_by_admin_id=admin_id,
        )
        self.db.add(message)
        self.db.flush()
        AuditLogService(self.db).record(
            admin_id=admin_id,
            action="broadcast_created",
            resource=f"broadcasts:{message.channel}",
            detail={
                "channel": message.channel,
                "scope": message.scope,
                "target_user_id": message.target_user_id,
                "title": message.title,
                "priority": message.priority,
                "starts_at": message.starts_at.isoformat() if message.starts_at else None,
                "ends_at": message.ends_at.isoformat() if message.ends_at else None,
            },
        )
        self.db.commit()
        self.db.refresh(message)
        return message

    def update_active(
        self,
        *,
        admin_id: str,
        message_id: str,
        payload: BroadcastToggleRequest,
    ) -> BroadcastMessage:
        message = self.db.get(BroadcastMessage, message_id)
        if message is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="消息不存在。")

        message.is_active = payload.is_active
        AuditLogService(self.db).record(
            admin_id=admin_id,
            action="broadcast_toggled",
            resource=f"broadcasts:{message.id}",
            detail={"channel": message.channel, "scope": message.scope, "is_active": payload.is_active},
        )
        self.db.commit()
        self.db.refresh(message)
        return message

    @staticmethod
    def status_of(message: BroadcastMessage) -> str:
        return _broadcast_status(message)
