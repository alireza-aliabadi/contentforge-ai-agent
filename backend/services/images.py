"""Image validation and vision metadata extraction."""

from __future__ import annotations

import base64
import io
from pathlib import Path

from PIL import Image

from backend.services.ai_client import AIClient

SUPPORTED_IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".svg"}
SUPPORTED_IMAGE_TYPES = {
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/svg+xml",
}


def is_supported_image(filename: str, content_type: str) -> bool:
    suffix = Path(filename).suffix.lower()
    return content_type in SUPPORTED_IMAGE_TYPES or suffix in SUPPORTED_IMAGE_SUFFIXES


def validate_and_describe_image(data: bytes, filename: str) -> dict:
    suffix = Path(filename).suffix.lower()
    meta: dict = {"filename": filename, "size_bytes": len(data), "format": suffix.lstrip(".")}
    if suffix == ".svg":
        meta["width"] = None
        meta["height"] = None
        meta["mode"] = "svg"
        return meta
    with Image.open(io.BytesIO(data)) as image:
        meta["width"] = image.width
        meta["height"] = image.height
        meta["mode"] = image.mode
    return meta


async def understand_image(data: bytes, filename: str, client: AIClient | None = None) -> dict:
    meta = validate_and_describe_image(data, filename)
    ai = client or AIClient()
    if Path(filename).suffix.lower() == ".svg":
        meta["vision_summary"] = "SVG graphic asset uploaded for brand/visual context."
        return meta
    b64 = base64.b64encode(data).decode("ascii")
    summary = await ai.describe_image(
        b64,
        "Describe this image for content creation context. Note subject, mood, and usable hooks.",
    )
    meta["vision_summary"] = summary
    return meta
