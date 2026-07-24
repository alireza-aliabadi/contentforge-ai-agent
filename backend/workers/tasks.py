"""Celery tasks."""

import asyncio
import logging
from uuid import UUID

from backend.db.session import async_session_factory
from backend.services.content import ContentService
from backend.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="contentforge.process_content_job")
def process_content_job(job_id: str) -> str:
    asyncio.run(_process(UUID(job_id)))
    return job_id


async def _process(job_id: UUID) -> None:
    service = ContentService()
    async with async_session_factory() as session:
        try:
            await service.process_job(session, job_id)
            await session.commit()
        except Exception:
            await session.rollback()
            logger.exception("Celery job failed: %s", job_id)
            raise
