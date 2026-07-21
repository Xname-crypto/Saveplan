from __future__ import annotations

import os
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent
BACKEND_DIR = APP_DIR.parent

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - optional local configuration helper
    load_dotenv = None

if load_dotenv is not None:
    load_dotenv(BACKEND_DIR / ".env", encoding="utf-8-sig")


def path_from_env(name: str, default: Path) -> Path:
    value = os.getenv(name)
    path = Path(value) if value else default
    if not path.is_absolute():
        path = BACKEND_DIR / path
    return path


def csv_env(name: str, default: tuple[str, ...] = ()) -> list[str]:
    value = os.getenv(name, "")
    values = [item.strip() for item in value.split(",") if item.strip()]
    return values or list(default)


DATA_DIR = path_from_env("SAVEPLAN_DATA_DIR", APP_DIR)
DATABASE_PATH = DATA_DIR / "saveplan.sqlite3"
UPLOAD_DIR = DATA_DIR / "uploads"
MEDIA_DIR = DATA_DIR / "conversion_media"

DEFAULT_CORS_ORIGINS = (
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
    "http://localhost:4173",
    "http://127.0.0.1:4173",
    "http://localhost:5178",
    "http://127.0.0.1:5178",
)
CORS_ORIGINS = csv_env("SAVEPLAN_PUBLIC_ORIGINS", DEFAULT_CORS_ORIGINS)
