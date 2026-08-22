from __future__ import annotations

from pydantic import BaseModel

from ..audit_logs.schema import AuditLogRead
from ..broadcasts.schema import BroadcastRead
from ..users.schema import UserAdminRead


class AdminDashboardSummaryRead(BaseModel):
    total_users: int
    new_users_24h: int
    new_users_7d: int
    active_redeem_codes: int
    active_announcements: int
    active_popups: int
    recent_users: list[UserAdminRead]
    recent_broadcasts: list[BroadcastRead]
    recent_logs: list[AuditLogRead]
