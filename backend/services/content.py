"""Content job orchestration service."""

from __future__ import annotations

import base64
import logging
import uuid
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.agents.pipeline import ContentPipeline
from backend.models.entities import (
    Asset,
    ContentJob,
    ContentPackage,
    ContentStatus,
    JobStatus,
    Platform,
)
from backend.services.storage import StorageService

logger = logging.getLogger(__name__)


class ContentService:
    def __init__(self) -> None:
        self.pipeline = ContentPipeline()
        self.storage = StorageService()

    async def create_job(
        self,
        session: AsyncSession,
        *,
        owner_id: UUID | None,
        prompt: str,
        platform: Platform,
        asset_ids: list[UUID],
    ) -> ContentJob:
        job = ContentJob(
            owner_id=owner_id,
            prompt=prompt,
            platform=platform,
            status=JobStatus.PENDING,
            asset_ids=[str(item) for item in asset_ids],
        )
        session.add(job)
        await session.flush()
        return job

    async def process_job(self, session: AsyncSession, job_id: UUID) -> ContentJob:
        result = await session.execute(
            select(ContentJob)
            .where(ContentJob.id == job_id)
            .options(selectinload(ContentJob.packages))
        )
        job = result.scalar_one()
        job.status = JobStatus.PROCESSING
        await session.flush()

        try:
            document_context, image_context = await self._gather_contexts(session, job)
            job.status = JobStatus.EVALUATING
            await session.flush()

            ctx = await self.pipeline.run(
                prompt=job.prompt,
                platform=job.platform,
                document_context=document_context,
                image_context=image_context,
            )

            if not ctx.evaluation.get("passed"):
                job.status = JobStatus.IMPROVING
                job.regeneration_count = max(0, len(ctx.history) - 3)

            banner_key = await self._persist_banner(ctx.banner_result, job.id)

            package = ContentPackage(
                job_id=job.id,
                title=ctx.draft_title,
                body=ctx.draft_body,
                platform=job.platform,
                status=ContentStatus.READY if ctx.evaluation.get("passed") else ContentStatus.DRAFT,
                originality_score=ctx.evaluation.get("originality"),
                relevance_score=ctx.evaluation.get("relevance"),
                expertise_score=ctx.evaluation.get("expertise"),
                banner_storage_key=banner_key,
                metadata_json={
                    "plan": ctx.plan,
                    "banner_prompt": ctx.banner_prompt,
                    "agent_history": ctx.history,
                    "banner": {k: v for k, v in ctx.banner_result.items() if k != "b64_json"},
                },
            )
            session.add(package)
            job.plan_json = ctx.plan
            job.evaluation_json = ctx.evaluation
            job.status = JobStatus.COMPLETED
            await session.flush()

            refreshed = await session.execute(
                select(ContentJob)
                .where(ContentJob.id == job.id)
                .options(selectinload(ContentJob.packages))
            )
            return refreshed.scalar_one()
        except Exception as exc:
            logger.exception("Content job %s failed", job_id)
            job.status = JobStatus.FAILED
            job.error_message = str(exc)
            await session.flush()
            raise

    async def _gather_contexts(self, session: AsyncSession, job: ContentJob) -> tuple[str, str]:
        if not job.asset_ids:
            return "", ""
        ids = [UUID(item) for item in job.asset_ids]
        result = await session.execute(select(Asset).where(Asset.id.in_(ids)))
        assets = list(result.scalars())
        docs = []
        images = []
        for asset in assets:
            if asset.asset_type.value == "document":
                docs.append(f"[{asset.filename}]\n{asset.extracted_text or ''}")
            else:
                vision = (asset.metadata_json or {}).get("vision_summary", "")
                images.append(f"[{asset.filename}] {vision}")
        return "\n\n".join(docs), "\n".join(images)

    async def _persist_banner(self, banner_result: dict, job_id: UUID) -> str | None:
        b64 = banner_result.get("b64_json")
        if b64:
            data = base64.b64decode(b64)
            return await self.storage.save_bytes(data, f"banner-{job_id}.png", folder="banners")
        # Mock mode: store a tiny placeholder marker file
        if banner_result.get("mock"):
            marker = f"mock-banner:{banner_result.get('prompt', '')}".encode()
            return await self.storage.save_bytes(
                marker,
                f"banner-{job_id}.txt",
                folder="banners",
            )
        return None


def new_job_id() -> uuid.UUID:
    return uuid.uuid4()
