from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from .crud import AuditLogCrud
from .model import AuditLog


class AuditLogService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.crud = AuditLogCrud(db)

    def record(
        self,
        *,
        admin_id: str | None,
        action: str,
        resource: str,
        detail: dict | None = None,
    ) -> AuditLog:
        return self.crud.create(
            AuditLog(
                id=str(uuid.uuid4()),
                admin_id=admin_id,
                action=action,
                resource=resource,
                detail=detail or {},
            )
        )

    def list_recent(self, limit: int = 100) -> list[AuditLog]:
        return self.crud.list_recent(limit)
