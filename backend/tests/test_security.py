"""Security helper tests."""

from backend.core.security import (
    Role,
    create_access_token,
    get_password_hash,
    has_permission,
    verify_password,
)


def test_password_hash_roundtrip() -> None:
    hashed = get_password_hash("secret123")
    assert verify_password("secret123", hashed)
    assert not verify_password("wrong", hashed)


def test_token_and_permissions() -> None:
    token = create_access_token("admin@contentforge.local", Role.ADMIN)
    assert isinstance(token, str)
    assert has_permission(Role.ADMIN, "content:write")
    assert has_permission(Role.CREATOR, "jobs:write")
    assert not has_permission(Role.VIEWER, "jobs:write")
