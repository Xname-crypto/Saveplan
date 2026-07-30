from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
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
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False,
)
_tables_initialized = False


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
    _tables_initialized = True


def ensure_database_initialized() -> None:
    if _tables_initialized:
        return
    init_database()
