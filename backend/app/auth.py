from __future__ import annotations

import sqlite3

from .config import DATABASE_PATH
from .modules.auth.controller import router
from .modules.auth.schema import (
    AuthResponse,
    AuthUser,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    LoginRequest,
    RegisterRequest,
    ResetPasswordRequest,
)
from .modules.auth.service import get_current_user, normalize_email


def get_connection() -> sqlite3.Connection:
    """Compatibility bridge for the legacy conversion module.

    The conversion/OCR code still stores conversion working data in the legacy
    SQLite table during this migration phase. User auth now uses SQLAlchemy.
    """
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_auth_db() -> None:
    """Compatibility no-op.

    SQLAlchemy tables are initialized from app.database.session.init_database()
    and production schema changes are managed by Alembic.
    """
    return None


__all__ = [
    "AuthResponse",
    "AuthUser",
    "ForgotPasswordRequest",
    "ForgotPasswordResponse",
    "LoginRequest",
    "RegisterRequest",
    "ResetPasswordRequest",
    "get_connection",
    "get_current_user",
    "init_auth_db",
    "normalize_email",
    "router",
]
