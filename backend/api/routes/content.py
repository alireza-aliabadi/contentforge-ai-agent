"""Content generation job routes."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.api.deps import require_permission
from backend.api.schemas import ContentJobCreate, ContentJobResponse, ImproveContentRequest
from backend.db.session import get_db
from backend.models.entities import ContentJob, ContentPackage, JobStatus, User
from backend.services.content import ContentService

router = APIRouter(prefix="/content", tags=["content"])
content_service = ContentService()


@router.post("/jobs", response_model=ContentJobResponse, status_code=status.HTTP_201_CREATED)
async def create_content_job(
    payload: ContentJobCreate,
    session: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_permission("jobs:write"))],
) -> ContentJob:
    job = await content_service.create_job(
        session,
        owner_id=user.id,
        prompt=payload.prompt,
        platform=payload.platform,
        asset_ids=payload.asset_ids,
    )
    await session.commit()

    # Process synchronously for local/dev simplicity; Celery task also available.
    try:
        job = await content_service.process_job(session, job.id)
        await session.commit()
    except Exception as exc:
        await session.rollback()
        result = await session.execute(select(ContentJob).where(ContentJob.id == job.id))
        failed = result.scalar_one()
        failed.status = JobStatus.FAILED
        failed.error_message = str(exc)
        await session.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Content generation failed: {exc}",
        ) from exc

    result = await session.execute(
        select(ContentJob).where(ContentJob.id == job.id).options(selectinload(ContentJob.packages))
    )
    return result.scalar_one()


@router.get("/jobs", response_model=list[ContentJobResponse])
async def list_jobs(
    session: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_permission("jobs:read"))],
) -> list[ContentJob]:
    result = await session.execute(
        select(ContentJob)
        .where(ContentJob.owner_id == user.id)
        .options(selectinload(ContentJob.packages))
        .order_by(ContentJob.created_at.desc())
    )
    return list(result.scalars())


@router.get("/jobs/{job_id}", response_model=ContentJobResponse)
async def get_job(
    job_id: UUID,
    session: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_permission("jobs:read"))],
) -> ContentJob:
    result = await session.execute(
        select(ContentJob).where(ContentJob.id == job_id).options(selectinload(ContentJob.packages))
    )
    job = result.scalar_one_or_none()
    if job is None or (job.owner_id and job.owner_id != user.id and user.role != "admin"):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return job


@router.post("/jobs/{job_id}/improve", response_model=ContentJobResponse)
async def improve_job(
    job_id: UUID,
    payload: ImproveContentRequest,
    session: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_permission("content:write"))],
) -> ContentJob:
    result = await session.execute(
        select(ContentJob).where(ContentJob.id == job_id).options(selectinload(ContentJob.packages))
    )
    job = result.scalar_one_or_none()
    if job is None or (job.owner_id and job.owner_id != user.id and user.role != "admin"):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    if not job.packages:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No package to improve")

    latest = job.packages[-1]
    from backend.agents.pipeline import AgentContext, ContentPipeline

    pipeline = ContentPipeline()
    ctx = AgentContext(
        prompt=job.prompt,
        platform=job.platform,
        draft_title=latest.title,
        draft_body=latest.body,
        evaluation=job.evaluation_json or {},
        plan=job.plan_json or {},
    )
    ctx = await pipeline.optimizer.run(ctx, instructions=payload.instructions)
    ctx = await pipeline.evaluator.run(ctx)
    ctx = await pipeline.banner.run(ctx)

    banner_key = await content_service._persist_banner(ctx.banner_result, job.id)
    package = ContentPackage(
        job_id=job.id,
        title=ctx.draft_title,
        body=ctx.draft_body,
        platform=job.platform,
        status=latest.status,
        originality_score=ctx.evaluation.get("originality"),
        relevance_score=ctx.evaluation.get("relevance"),
        expertise_score=ctx.evaluation.get("expertise"),
        banner_storage_key=banner_key,
        metadata_json={"improved": True, "instructions": payload.instructions},
    )
    session.add(package)
    job.evaluation_json = ctx.evaluation
    job.regeneration_count += 1
    await session.flush()

    refreshed = await session.execute(
        select(ContentJob).where(ContentJob.id == job.id).options(selectinload(ContentJob.packages))
    )
    return refreshed.scalar_one()
