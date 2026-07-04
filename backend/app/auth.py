from __future__ import annotations

import hashlib
import hmac
import json
import base64
import os
import secrets
import sqlite3
import time
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from pydantic import BaseModel, Field

DATABASE_PATH = Path(__file__).resolve().parent / "saveplan.sqlite3"
PBKDF2_ITERATIONS = 260_000
RESET_TOKEN_MINUTES = 60
SESSION_DAYS = 30
JWT_ALGORITHM = "HS256"
JWT_SECRET = os.environ.get("SAVEPLAN_JWT_SECRET", "saveplan-local-dev-jwt-secret")

router = APIRouter(prefix="/api/auth", tags=["auth"])


class AuthUser(BaseModel):
    id: str
    email: str
    username: str
    job: str | None = None
    bio: str | None = None
    interests: list[str] = Field(default_factory=list)
    avatar_name: str | None = None
    created_at: str


class AuthResponse(BaseModel):
    token: str
    user: AuthUser


class RegisterRequest(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=6, max_length=128)
    username: str = Field(min_length=3, max_length=80)
    job: str = Field(min_length=1, max_length=120)
    bio: str | None = Field(default=None, max_length=600)
    interests: list[str] = Field(default_factory=list, max_length=12)
    avatar_name: str | None = Field(default=None, max_length=255)


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=1, max_length=128)


class ForgotPasswordRequest(BaseModel):
    email: str = Field(min_length=3, max_length=254)


class ForgotPasswordResponse(BaseModel):
    message: str
    reset_token: str | None = None
    reset_url: str | None = None


class ResetPasswordRequest(BaseModel):
    token: str = Field(min_length=16)
    password: str = Field(min_length=6, max_length=128)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def iso_now() -> str:
    return utc_now().isoformat()


def session_expires_at() -> str:
    return (utc_now() + timedelta(days=SESSION_DAYS)).isoformat()


def get_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_auth_db() -> None:
    with get_connection() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                password_salt TEXT NOT NULL,
                username TEXT NOT NULL,
                job TEXT,
                bio TEXT,
                interests TEXT NOT NULL DEFAULT '[]',
                avatar_name TEXT,
                token_version INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS sessions (
                token TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS password_resets (
                token TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );
            """
        )
        user_columns = {
            row["name"] for row in connection.execute("PRAGMA table_info(users)").fetchall()
        }
        if "token_version" not in user_columns:
            connection.execute(
                "ALTER TABLE users ADD COLUMN token_version INTEGER NOT NULL DEFAULT 0"
            )

        existing_columns = {
            row["name"] for row in connection.execute("PRAGMA table_info(sessions)").fetchall()
        }
        if "expires_at" not in existing_columns:
            connection.execute("ALTER TABLE sessions ADD COLUMN expires_at TEXT")
            connection.execute(
                "UPDATE sessions SET expires_at = ? WHERE expires_at IS NULL",
                (session_expires_at(),),
            )


def normalize_email(email: str) -> str:
    normalized = email.strip().lower()
    if "@" not in normalized or "." not in normalized.rsplit("@", 1)[-1]:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="请输入有效的邮箱地址。",
        )
    return normalized


def hash_password(password: str, salt: bytes | None = None) -> tuple[str, str]:
    password_salt = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        password_salt,
        PBKDF2_ITERATIONS,
    )
    return digest.hex(), password_salt.hex()


def verify_password(password: str, stored_hash: str, stored_salt: str) -> bool:
    digest, _salt = hash_password(password, bytes.fromhex(stored_salt))
    return hmac.compare_digest(digest, stored_hash)


def base64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def base64url_decode(data: str) -> bytes:
    padded = data + "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(padded.encode("ascii"))


def sign_jwt_part(signing_input: str) -> str:
    signature = hmac.new(
        JWT_SECRET.encode("utf-8"),
        signing_input.encode("ascii"),
        hashlib.sha256,
    ).digest()
    return base64url_encode(signature)


def create_jwt(user_id: str, token_version: int) -> str:
    now = int(time.time())
    header = {"alg": JWT_ALGORITHM, "typ": "JWT"}
    payload = {
        "sub": user_id,
        "token_version": token_version,
        "iat": now,
        "exp": now + SESSION_DAYS * 24 * 60 * 60,
    }
    signing_input = ".".join(
        [
            base64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8")),
            base64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8")),
        ]
    )
    return f"{signing_input}.{sign_jwt_part(signing_input)}"


def verify_jwt(token: str) -> dict[str, object]:
    try:
        header_part, payload_part, signature_part = token.split(".", 2)
        signing_input = f"{header_part}.{payload_part}"
        expected_signature = sign_jwt_part(signing_input)
        if not hmac.compare_digest(signature_part, expected_signature):
            raise ValueError("Bad signature")

        header = json.loads(base64url_decode(header_part))
        if header.get("alg") != JWT_ALGORITHM:
            raise ValueError("Unsupported algorithm")

        payload = json.loads(base64url_decode(payload_part))
        if int(payload.get("exp", 0)) < int(time.time()):
            raise ValueError("Expired token")
        return payload
    except (ValueError, TypeError, json.JSONDecodeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired. Please sign in again.",
        ) from None


def row_to_user(row: sqlite3.Row) -> AuthUser:
    try:
        interests = json.loads(row["interests"] or "[]")
    except json.JSONDecodeError:
        interests = []

    return AuthUser(
        id=row["id"],
        email=row["email"],
        username=row["username"],
        job=row["job"],
        bio=row["bio"],
        interests=interests if isinstance(interests, list) else [],
        avatar_name=row["avatar_name"],
        created_at=row["created_at"],
    )


def create_session(connection: sqlite3.Connection, user_id: str) -> str:
    token = secrets.token_urlsafe(32)
    connection.execute(
        "INSERT INTO sessions (token, user_id, created_at, expires_at) VALUES (?, ?, ?, ?)",
        (token, user_id, iso_now(), session_expires_at()),
    )
    return token


def get_current_user(
    authorization: Annotated[str | None, Header()] = None,
) -> AuthUser:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="请先登录。",
        )

    token = authorization.removeprefix("Bearer ").strip()
    payload = verify_jwt(token)
    user_id = payload.get("sub")
    token_version = payload.get("token_version")

    if not isinstance(user_id, str) or not isinstance(token_version, int):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired. Please sign in again.",
        )

    with get_connection() as connection:
        row = connection.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()

    if row is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="登录状态已失效，请重新登录。",
        )

    if row["token_version"] != token_version:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired. Please sign in again.",
        )

    return row_to_user(row)


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest) -> AuthResponse:
    email = normalize_email(payload.email)
    password_hash, password_salt = hash_password(payload.password)
    user_id = str(uuid.uuid4())

    with get_connection() as connection:
        existing = connection.execute(
            "SELECT id FROM users WHERE email = ?",
            (email,),
        ).fetchone()

        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="这个邮箱已经注册过，请直接登录。",
            )

        connection.execute(
            """
            INSERT INTO users (
                id, email, password_hash, password_salt, username, job, bio,
                interests, avatar_name, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                email,
                password_hash,
                password_salt,
                payload.username.strip(),
                payload.job.strip(),
                payload.bio,
                json.dumps(payload.interests, ensure_ascii=False),
                payload.avatar_name,
                iso_now(),
            ),
        )
        row = connection.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()

    return AuthResponse(token=create_jwt(row["id"], row["token_version"]), user=row_to_user(row))


@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest) -> AuthResponse:
    email = normalize_email(payload.email)

    with get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM users WHERE email = ?",
            (email,),
        ).fetchone()

        if row is None or not verify_password(
            payload.password,
            row["password_hash"],
            row["password_salt"],
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="邮箱或密码不正确，请检查后重试。",
            )

    return AuthResponse(token=create_jwt(row["id"], row["token_version"]), user=row_to_user(row))


@router.post("/forgot-password", response_model=ForgotPasswordResponse)
def forgot_password(payload: ForgotPasswordRequest, request: Request) -> ForgotPasswordResponse:
    email = normalize_email(payload.email)
    message = "如果该邮箱已注册，重置链接已经生成。"

    with get_connection() as connection:
        row = connection.execute(
            "SELECT id FROM users WHERE email = ?",
            (email,),
        ).fetchone()

        if row is None:
            return ForgotPasswordResponse(message=message)

        token = secrets.token_urlsafe(32)
        expires_at = (utc_now() + timedelta(minutes=RESET_TOKEN_MINUTES)).isoformat()
        connection.execute("DELETE FROM password_resets WHERE user_id = ?", (row["id"],))
        connection.execute(
            """
            INSERT INTO password_resets (token, user_id, expires_at, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (token, row["id"], expires_at, iso_now()),
        )

    origin = request.headers.get("origin") or str(request.base_url).rstrip("/")
    reset_url = f"{origin}/reset-password?token={token}"
    return ForgotPasswordResponse(message=message, reset_token=token, reset_url=reset_url)


@router.post("/reset-password")
def reset_password(payload: ResetPasswordRequest) -> dict[str, str]:
    with get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM password_resets WHERE token = ?",
            (payload.token,),
        ).fetchone()

        if row is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="重置链接无效或已经使用。",
            )

        expires_at = datetime.fromisoformat(row["expires_at"])
        if expires_at < utc_now():
            connection.execute("DELETE FROM password_resets WHERE token = ?", (payload.token,))
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="重置链接已过期，请重新发送。",
            )

        password_hash, password_salt = hash_password(payload.password)
        connection.execute(
            """
            UPDATE users
            SET password_hash = ?, password_salt = ?, token_version = token_version + 1
            WHERE id = ?
            """,
            (password_hash, password_salt, row["user_id"]),
        )
        connection.execute("DELETE FROM password_resets WHERE token = ?", (payload.token,))
        connection.execute("DELETE FROM sessions WHERE user_id = ?", (row["user_id"],))

    return {"message": "密码已更新。"}


@router.get("/me", response_model=AuthUser)
def me(current_user: Annotated[AuthUser, Depends(get_current_user)]) -> AuthUser:
    return current_user
