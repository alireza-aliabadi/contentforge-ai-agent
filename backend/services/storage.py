"""Local filesystem / object storage helpers."""

from __future__ import annotations

import uuid
from pathlib import Path

import aiofiles

from backend.core.config import get_settings


class StorageService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.root = Path(self.settings.local_storage_path)
        self.root.mkdir(parents=True, exist_ok=True)

    async def save_bytes(self, data: bytes, filename: str, folder: str = "assets") -> str:
        safe_name = Path(filename).name
        key = f"{folder}/{uuid.uuid4().hex}_{safe_name}"
        path = self.root / key
        path.parent.mkdir(parents=True, exist_ok=True)
        async with aiofiles.open(path, "wb") as handle:
            await handle.write(data)
        return key

    def resolve_path(self, storage_key: str) -> Path:
        return self.root / storage_key

    async def read_bytes(self, storage_key: str) -> bytes:
        path = self.resolve_path(storage_key)
        async with aiofiles.open(path, "rb") as handle:
            return await handle.read()
