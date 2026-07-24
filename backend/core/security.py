"""JWT authentication and password hashing."""

from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import Any

import bcrypt
from jose import JWTError, jwt

from backend.core.config import Settings, get_settings


class Role(StrEnum):
    ADMIN = "admin"
    CREATOR = "creator"
    EDITOR = "editor"
    VIEWER = "viewer"


ROLE_PERMISSIONS: dict[Role, set[str]] = {
    Role.ADMIN: {"*"},
    Role.CREATOR: {
        "content:read",
        "content:write",
        "assets:read",
        "assets:write",
        "jobs:read",
        "jobs:write",
    },
    Role.EDITOR: {
        "content:read",
        "content:write",
        "assets:read",
        "jobs:read",
    },
    Role.VIEWER: {"content:read", "assets:read", "jobs:read"},
}


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())


def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def create_access_token(
    subject: str,
    role: Role,
    settings: Settings | None = None,
    expires_delta: timedelta | None = None,
) -> str:
    cfg = settings or get_settings()
    expire = datetime.now(UTC) + (
        expires_delta or timedelta(minutes=cfg.access_token_expire_minutes)
    )
    payload = {"sub": subject, "role": role.value, "exp": expire}
    return jwt.encode(payload, cfg.secret_key, algorithm=cfg.jwt_algorithm)


def decode_access_token(token: str, settings: Settings | None = None) -> dict[str, Any]:
    cfg = settings or get_settings()
    try:
        return jwt.decode(token, cfg.secret_key, algorithms=[cfg.jwt_algorithm])
    except JWTError as exc:
        raise ValueError("Invalid token") from exc


def has_permission(role: Role, permission: str) -> bool:
    allowed = ROLE_PERMISSIONS.get(role, set())
    return "*" in allowed or permission in allowed
