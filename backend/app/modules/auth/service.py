from __future__ import annotations

import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from ...config import INITIAL_USER_POINTS, JWT_SECRET
from ...core.security import create_token, hash_password, utc_now, verify_password, verify_token
from ...database.session import get_db
from ..users.model import User
from .crud import AuthCrud
from .model import PasswordReset
from .schema import AuthResponse, AuthUser, ForgotPasswordResponse, RegisterRequest

RESET_TOKEN_MINUTES = 60
SESSION_DAYS = 30
SESSION_MINUTES = SESSION_DAYS * 24 * 60


def as_aware_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def normalize_email(email: str) -> str:
    normalized = email.strip().lower()
    if "@" not in normalized or "." not in normalized.rsplit("@", 1)[-1]:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="请输入有效的邮箱地址。",
        )
    return normalized


def user_to_schema(user: User) -> AuthUser:
    points = user.point_balance or 0
    return AuthUser(
        id=user.id,
        email=user.email,
        username=user.username,
        job=user.job,
        bio=user.bio,
        interests=user.interests if isinstance(user.interests, list) else [],
        avatar_name=user.avatar_name,
        points=points,
        credits=points,
        created_at=user.created_at.isoformat(),
    )


def create_user_token(user: User) -> str:
    return create_token(
        subject=user.id,
        secret=JWT_SECRET,
        expires_minutes=SESSION_MINUTES,
        payload={
            "type": "user",
            "token_version": user.token_version,
        },
    )


class AuthService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.crud = AuthCrud(db)

    def register(self, payload: RegisterRequest) -> AuthResponse:
        email = normalize_email(payload.email)
        if self.crud.get_user_by_email(email) is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="这个邮箱已经注册过，请直接登录。",
            )

        password_hash, password_salt = hash_password(payload.password)
        user = self.crud.create_user(
            User(
                id=str(uuid.uuid4()),
                email=email,
                password_hash=password_hash,
                password_salt=password_salt,
                username=payload.username.strip(),
                job=payload.job.strip(),
                bio=payload.bio,
                interests=payload.interests,
                avatar_name=payload.avatar_name,
                point_balance=INITIAL_USER_POINTS,
            )
        )
        self.db.commit()
        self.db.refresh(user)
        return AuthResponse(token=create_user_token(user), user=user_to_schema(user))

    def login(self, email: str, password: str) -> AuthResponse:
        user = self.crud.get_user_by_email(normalize_email(email))
        if user is None or not verify_password(password, user.password_hash, user.password_salt):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="邮箱或密码不正确，请检查后重试。",
            )
        return AuthResponse(token=create_user_token(user), user=user_to_schema(user))

    def forgot_password(self, email: str, origin: str) -> ForgotPasswordResponse:
        normalized_email = normalize_email(email)
        message = "如果该邮箱已注册，重置链接已经生成。"
        user = self.crud.get_user_by_email(normalized_email)
        if user is None:
            return ForgotPasswordResponse(message=message)

        token = secrets.token_urlsafe(32)
        self.crud.delete_password_resets_for_user(user.id)
        self.crud.create_password_reset(
            PasswordReset(
                token=token,
                user_id=user.id,
                expires_at=utc_now() + timedelta(minutes=RESET_TOKEN_MINUTES),
            )
        )
        self.db.commit()
        return ForgotPasswordResponse(
            message=message,
            reset_token=token,
            reset_url=f"{origin}/reset-password?token={token}",
        )

    def reset_password(self, token: str, password: str) -> dict[str, str]:
        reset = self.crud.get_password_reset(token)
        if reset is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="重置链接无效或已经使用。",
            )

        if as_aware_utc(reset.expires_at) < utc_now():
            self.crud.delete_password_reset(token)
            self.db.commit()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="重置链接已过期，请重新发送。",
            )

        user = self.crud.get_user_by_id(reset.user_id)
        if user is None:
            self.crud.delete_password_reset(token)
            self.db.commit()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="重置链接无效或已经使用。",
            )

        password_hash, password_salt = hash_password(password)
        user.password_hash = password_hash
        user.password_salt = password_salt
        user.token_version += 1
        self.crud.delete_password_reset(token)
        self.db.commit()
        return {"message": "密码已更新。"}


def get_current_user(
    db: Annotated[Session, Depends(get_db)],
    authorization: Annotated[str | None, Header()] = None,
) -> AuthUser:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="请先登录。",
        )

    token = authorization.removeprefix("Bearer ").strip()
    payload = verify_token(token, JWT_SECRET)
    user_id = payload.get("sub")
    token_type = payload.get("type", "user")
    token_version = payload.get("token_version")

    if token_type != "user" or not isinstance(user_id, str) or not isinstance(token_version, int):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired. Please sign in again.",
        )

    user = AuthCrud(db).get_user_by_id(user_id)
    if user is None or user.token_version != token_version:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="登录状态已失效，请重新登录。",
        )
    return user_to_schema(user)
