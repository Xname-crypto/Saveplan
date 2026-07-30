from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import time
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import HTTPException, status

PBKDF2_ITERATIONS = 260_000
JWT_ALGORITHM = "HS256"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


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


def _sign(signing_input: str, secret: str) -> str:
    signature = hmac.new(
        secret.encode("utf-8"),
        signing_input.encode("ascii"),
        hashlib.sha256,
    ).digest()
    return base64url_encode(signature)


def create_token(
    *,
    subject: str,
    secret: str,
    expires_minutes: int,
    payload: dict[str, Any] | None = None,
) -> str:
    now = int(time.time())
    header = {"alg": JWT_ALGORITHM, "typ": "JWT"}
    body = {
        "sub": subject,
        "iat": now,
        "exp": int((utc_now() + timedelta(minutes=expires_minutes)).timestamp()),
        **(payload or {}),
    }
    signing_input = ".".join(
        [
            base64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8")),
            base64url_encode(json.dumps(body, separators=(",", ":")).encode("utf-8")),
        ]
    )
    return f"{signing_input}.{_sign(signing_input, secret)}"


def verify_token(token: str, secret: str) -> dict[str, Any]:
    try:
        header_part, payload_part, signature_part = token.split(".", 2)
        signing_input = f"{header_part}.{payload_part}"
        if not hmac.compare_digest(signature_part, _sign(signing_input, secret)):
            raise ValueError("bad signature")

        header = json.loads(base64url_decode(header_part))
        if header.get("alg") != JWT_ALGORITHM:
            raise ValueError("unsupported algorithm")

        payload = json.loads(base64url_decode(payload_part))
        if int(payload.get("exp", 0)) < int(time.time()):
            raise ValueError("expired token")
        return payload
    except (ValueError, TypeError, json.JSONDecodeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="登录状态已失效，请重新登录。",
        ) from None
