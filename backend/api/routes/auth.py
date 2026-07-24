"""Authentication routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_current_user
from backend.api.schemas import LoginRequest, RegisterRequest, TokenResponse, UserResponse
from backend.core.config import get_settings
from backend.core.security import Role, create_access_token, get_password_hash, verify_password
from backend.db.session import get_db
from backend.models.entities import User

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    payload: RegisterRequest,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    existing = await session.execute(select(User).where(User.email == payload.email))
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
    user = User(
        email=payload.email,
        hashed_password=get_password_hash(payload.password),
        full_name=payload.full_name,
        role=Role.CREATOR.value,
    )
    session.add(user)
    await session.flush()
    return user


@router.post("/login", response_model=TokenResponse)
async def login(
    payload: LoginRequest,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> TokenResponse:
    result = await session.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()
    if user is None or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = create_access_token(subject=user.email, role=Role(user.role))
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserResponse)
async def me(user: Annotated[User, Depends(get_current_user)]) -> User:
    return user


async def ensure_default_admin(session: AsyncSession) -> None:
    settings = get_settings()
    result = await session.execute(select(User).where(User.email == settings.default_admin_email))
    if result.scalar_one_or_none() is None:
        admin = User(
            email=settings.default_admin_email,
            hashed_password=get_password_hash(settings.default_admin_password),
            full_name="ContentForge Admin",
            role=Role.ADMIN.value,
        )
        session.add(admin)
        await session.commit()
