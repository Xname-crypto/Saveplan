from __future__ import annotations

from datetime import timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ...core.security import utc_now
from ..audit_logs.schema import AuditLogRead
from ..audit_logs.service import AuditLogService
from ..broadcasts.model import BroadcastMessage
from ..broadcasts.schema import BroadcastRead
from ..broadcasts.service import BroadcastService
from ..redeem_codes.model import RedeemCode
from ..users.model import User
from ..users.schema import UserAdminRead
from .schema import AdminDashboardSummaryRead


def _as_read_broadcast(service: BroadcastService, message: BroadcastMessage) -> BroadcastRead:
    base = BroadcastRead.model_validate(message)
    return base.model_copy(update={"status": service.status_of(message)})


class AdminDashboardService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def summary(self) -> AdminDashboardSummaryRead:
        now = utc_now()
        since_24h = now - timedelta(hours=24)
        since_7d = now - timedelta(days=7)
        broadcast_service = BroadcastService(self.db)

        total_users = self.db.scalar(select(func.count(User.id))) or 0
        new_users_24h = self.db.scalar(select(func.count(User.id)).where(User.created_at >= since_24h)) or 0
        new_users_7d = self.db.scalar(select(func.count(User.id)).where(User.created_at >= since_7d)) or 0
        active_redeem_codes = (
            self.db.scalar(
                select(func.count(RedeemCode.id))
                .where(RedeemCode.is_active.is_(True))
                .where((RedeemCode.expires_at.is_(None)) | (RedeemCode.expires_at >= now))
            )
            or 0
        )
        active_announcements = (
            self.db.scalar(
                select(func.count(BroadcastMessage.id))
                .where(BroadcastMessage.channel == "announcement")
                .where(BroadcastMessage.scope == "global")
                .where(BroadcastMessage.is_active.is_(True))
                .where((BroadcastMessage.starts_at.is_(None)) | (BroadcastMessage.starts_at <= now))
                .where((BroadcastMessage.ends_at.is_(None)) | (BroadcastMessage.ends_at >= now))
            )
            or 0
        )
        active_popups = (
            self.db.scalar(
                select(func.count(BroadcastMessage.id))
                .where(BroadcastMessage.channel == "popup")
                .where(BroadcastMessage.is_active.is_(True))
                .where((BroadcastMessage.starts_at.is_(None)) | (BroadcastMessage.starts_at <= now))
                .where((BroadcastMessage.ends_at.is_(None)) | (BroadcastMessage.ends_at >= now))
            )
            or 0
        )

        recent_users = list(
            self.db.scalars(select(User).order_by(User.created_at.desc()).limit(5)).all()
        )
        recent_broadcasts = [
            _as_read_broadcast(broadcast_service, message)
            for message in broadcast_service.list_messages(5)
        ]
        recent_logs = AuditLogService(self.db).list_recent(8)

        return AdminDashboardSummaryRead(
            total_users=total_users,
            new_users_24h=new_users_24h,
            new_users_7d=new_users_7d,
            active_redeem_codes=active_redeem_codes,
            active_announcements=active_announcements,
            active_popups=active_popups,
            recent_users=[UserAdminRead.model_validate(item) for item in recent_users],
            recent_broadcasts=recent_broadcasts,
            recent_logs=[AuditLogRead.model_validate(item) for item in recent_logs],
        )
