"""Platform metadata routes."""

from fastapi import APIRouter

from backend.api.schemas import PlatformInfo
from backend.services.platforms import list_platforms

router = APIRouter(prefix="/platforms", tags=["platforms"])


@router.get("", response_model=list[PlatformInfo])
async def platforms() -> list[PlatformInfo]:
    return list_platforms()
