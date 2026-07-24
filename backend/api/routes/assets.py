"""Asset upload routes for documents and images."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_current_user, require_permission
from backend.api.schemas import AssetResponse
from backend.db.session import get_db
from backend.models.entities import Asset, AssetType, User
from backend.services.documents import detect_document_kind, extract_text
from backend.services.images import is_supported_image, understand_image
from backend.services.storage import StorageService

router = APIRouter(prefix="/assets", tags=["assets"])
storage = StorageService()


@router.post("/documents", response_model=AssetResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    session: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_permission("assets:write"))],
    file: Annotated[UploadFile, File()],
) -> Asset:
    data = await file.read()
    if not data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Empty file")
    filename = file.filename or "document.txt"
    content_type = file.content_type or "application/octet-stream"
    kind = detect_document_kind(filename, content_type)
    if kind is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported document type. Use PDF, DOCX, TXT, Markdown, or CSV.",
        )
    try:
        text = extract_text(data, kind)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to extract text: {exc}",
        ) from exc

    key = await storage.save_bytes(data, filename, folder="documents")
    asset = Asset(
        owner_id=user.id,
        filename=filename,
        content_type=content_type,
        asset_type=AssetType.DOCUMENT,
        storage_key=key,
        extracted_text=text,
        metadata_json={"kind": kind, "chars": len(text)},
    )
    session.add(asset)
    await session.flush()
    return asset


@router.post("/images", response_model=AssetResponse, status_code=status.HTTP_201_CREATED)
async def upload_image(
    session: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_permission("assets:write"))],
    file: Annotated[UploadFile, File()],
) -> Asset:
    data = await file.read()
    if not data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Empty file")
    filename = file.filename or "image.png"
    content_type = file.content_type or "application/octet-stream"
    if not is_supported_image(filename, content_type):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported image type. Use JPG, PNG, or SVG.",
        )
    meta = await understand_image(data, filename)
    key = await storage.save_bytes(data, filename, folder="images")
    asset = Asset(
        owner_id=user.id,
        filename=filename,
        content_type=content_type,
        asset_type=AssetType.IMAGE,
        storage_key=key,
        extracted_text=meta.get("vision_summary"),
        metadata_json=meta,
    )
    session.add(asset)
    await session.flush()
    return asset


@router.get("", response_model=list[AssetResponse])
async def list_assets(
    session: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_permission("assets:read"))],
) -> list[Asset]:
    result = await session.execute(
        select(Asset).where(Asset.owner_id == user.id).order_by(Asset.created_at.desc())
    )
    return list(result.scalars())


@router.get("/{asset_id}", response_model=AssetResponse)
async def get_asset(
    asset_id: UUID,
    session: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> Asset:
    result = await session.execute(select(Asset).where(Asset.id == asset_id))
    asset = result.scalar_one_or_none()
    if asset is None or (asset.owner_id and asset.owner_id != user.id and user.role != "admin"):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")
    return asset
