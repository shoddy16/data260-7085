"""HW7 JWT authentication and role authorization without a new auth scheme."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import time
from collections.abc import Callable
from typing import Any

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from database.database import get_db
from models.models import User

JWT_SECRET = os.getenv("HW7_JWT_SECRET", "hw7-local-development-secret")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_SECONDS = int(os.getenv("HW7_JWT_EXPIRE_SECONDS", "1800"))
ROLES = {"reader", "writer", "moderator"}
bearer = HTTPBearer(auto_error=False)


def hash_password(password: str, salt: bytes | None = None) -> str:
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 210_000)
    return "pbkdf2_sha256$210000$%s$%s" % (
        base64.urlsafe_b64encode(salt).decode().rstrip("="),
        base64.urlsafe_b64encode(digest).decode().rstrip("="),
    )


def verify_password(password: str, encoded: str) -> bool:
    try:
        scheme, rounds, salt_text, digest_text = encoded.split("$", 3)
        if scheme != "pbkdf2_sha256":
            return False
        padding = "=" * (-len(salt_text) % 4)
        salt = base64.urlsafe_b64decode(salt_text + padding)
        expected = hash_password(password, salt).split("$", 3)[3]
        return int(rounds) == 210_000 and hmac.compare_digest(expected, digest_text)
    except (ValueError, TypeError):
        return False


def _b64(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode().rstrip("=")


def _unb64(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def create_access_token(username: str, role: str) -> str:
    now = int(time.time())
    header = {"alg": JWT_ALGORITHM, "typ": "JWT"}
    payload = {"sub": username, "role": role, "iat": now, "exp": now + JWT_EXPIRE_SECONDS}
    encoded = ".".join(_b64(json.dumps(part, separators=(",", ":")).encode()) for part in (header, payload))
    signature = hmac.new(JWT_SECRET.encode(), encoded.encode(), hashlib.sha256).digest()
    return encoded + "." + _b64(signature)


def decode_access_token(token: str) -> dict[str, Any]:
    try:
        encoded_header, encoded_payload, encoded_signature = token.split(".")
        signed = f"{encoded_header}.{encoded_payload}".encode()
        expected = hmac.new(JWT_SECRET.encode(), signed, hashlib.sha256).digest()
        if not hmac.compare_digest(expected, _unb64(encoded_signature)):
            raise ValueError("bad signature")
        header = json.loads(_unb64(encoded_header))
        payload = json.loads(_unb64(encoded_payload))
        if header.get("alg") != JWT_ALGORITHM or int(payload.get("exp", 0)) < int(time.time()):
            raise ValueError("expired token")
        if not isinstance(payload.get("sub"), str) or payload.get("role") not in ROLES:
            raise ValueError("invalid claims")
        return payload
    except (ValueError, TypeError, KeyError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise HTTPException(
            status_code=401, detail="Invalid or expired bearer token", headers={"WWW-Authenticate": "Bearer"}
        ) from exc


def authenticate_user(db: Session, username: str, password: str) -> User | None:
    user = db.query(User).filter(User.username == username).first()
    if user and user.role in ROLES and verify_password(password, user.password_hash):
        return user
    return None


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Bearer token required", headers={"WWW-Authenticate": "Bearer"})
    claims = decode_access_token(credentials.credentials)
    user = db.query(User).filter(User.username == claims["sub"]).first()
    if user is None or user.role != claims.get("role"):
        raise HTTPException(status_code=401, detail="Invalid bearer identity", headers={"WWW-Authenticate": "Bearer"})
    return user


def require_roles(*allowed: str) -> Callable:
    allowed_set = set(allowed)

    def checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in allowed_set:
            raise HTTPException(status_code=403, detail="Insufficient role for this operation")
        return user

    return checker
