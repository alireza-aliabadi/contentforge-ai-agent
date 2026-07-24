"""Health check routes."""

from fastapi import APIRouter

from backend.api.schemas import HealthResponse
from backend.core.config import get_settings

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(status="ok", app=settings.app_name, env=settings.app_env)
