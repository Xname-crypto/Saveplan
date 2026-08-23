from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine, event, inspect
from sqlalchemy.orm import Session, sessionmaker

from ..config import AUTO_CREATE_TABLES, DATABASE_URL
from .base import Base


def _connect_args() -> dict[str, object]:
    if DATABASE_URL.startswith("sqlite"):
        return {"check_same_thread": False}
    return {}


engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    connect_args=_connect_args(),
)

if DATABASE_URL.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, _connection_record) -> None:  # type: ignore[unused-ignore]
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False,
)
_tables_initialized = False


def _ensure_point_transaction_redeem_code_column() -> None:
    inspector = inspect(engine)
    if "point_transactions" not in inspector.get_table_names():
        return

    columns = {column["name"] for column in inspector.get_columns("point_transactions")}
    if "redeem_code_id" in columns:
        return

    with engine.begin() as connection:
        connection.exec_driver_sql("ALTER TABLE point_transactions ADD COLUMN redeem_code_id VARCHAR(36)")


def get_db() -> Generator[Session, None, None]:
    ensure_database_initialized()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_database() -> None:
    global _tables_initialized
    if not AUTO_CREATE_TABLES:
        return
    from . import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    _ensure_point_transaction_redeem_code_column()
    _tables_initialized = True


def ensure_database_initialized() -> None:
    if _tables_initialized:
        return
    init_database()
