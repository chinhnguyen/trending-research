import asyncio
import logging
import uuid
from datetime import datetime, timezone

from willbe_trends.config import get_settings
from willbe_trends.db.models import SessionLocal
from willbe_trends.db.repository import (
    _content_idea_to_schema,
    create_media_job,
    get_content_idea_row,
    get_media_job,
    idea_needs_media,
    list_resumable_media_jobs,
    media_job_to_schema,
    update_content_idea,
    update_media_job,
)
from willbe_trends.media.diagnostics import is_image_generation_allowed
from willbe_trends.media.service import enrich_content_idea_media
from willbe_trends.models.briefs import ContentIdea
from willbe_trends.models.media_jobs import ACTIVE_MEDIA_JOB_STATUSES, MediaJobStatus

logger = logging.getLogger(__name__)

_running_jobs: set[str] = set()


def _now() -> datetime:
    return datetime.now(timezone.utc)


async def _progress_for_job(job_id: str):
    async def callback(stage: str, percent: int) -> None:
        session = SessionLocal()
        try:
            update_media_job(
                session,
                job_id,
                status="generating_media",
                stage=stage,
                progress_percent=max(0, min(100, percent)),
            )
        finally:
            session.close()

    return callback


async def run_media_job(job_id: str) -> None:
    if job_id in _running_jobs:
        return
    _running_jobs.add(job_id)
    session = SessionLocal()
    try:
        job = get_media_job(session, job_id)
        if job is None or job.status not in ACTIVE_MEDIA_JOB_STATUSES:
            return

        update_media_job(
            session,
            job_id,
            status="generating_media",
            stage="Preparing media generation…",
            progress_percent=5,
        )

        idea_row = get_content_idea_row(session, job.content_idea_id)
        if idea_row is None:
            update_media_job(
                session,
                job_id,
                status="failed",
                stage="Content idea not found",
                progress_percent=0,
                error_message="The content idea for this job no longer exists.",
                completed_at=_now(),
            )
            return

        idea = _content_idea_to_schema(idea_row)
        if idea is None:
            update_media_job(
                session,
                job_id,
                status="failed",
                stage="Content idea could not be loaded",
                progress_percent=0,
                error_message="The content idea could not be loaded.",
                completed_at=_now(),
            )
            return

        progress = await _progress_for_job(job_id)
        enriched = await enrich_content_idea_media(
            idea,
            settings=get_settings(),
            on_progress=progress,
        )
        update_content_idea(session, job.content_idea_id, enriched)
        update_media_job(
            session,
            job_id,
            status="completed",
            stage="Media ready",
            progress_percent=100,
            completed_at=_now(),
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("Media job %s failed", job_id)
        try:
            update_media_job(
                session,
                job_id,
                status="failed",
                stage="Media generation failed",
                progress_percent=0,
                error_message=str(exc),
                completed_at=_now(),
            )
        except Exception:  # noqa: BLE001
            logger.exception("Could not persist failure for media job %s", job_id)
    finally:
        session.close()
        _running_jobs.discard(job_id)


def _schedule_task(job_id: str) -> None:
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        asyncio.run(run_media_job(job_id))
        return
    loop.create_task(run_media_job(job_id))


def schedule_media_job_for_idea(
    session,
    *,
    content_idea: ContentIdea,
    brief_item_id: str,
    brief_id: str,
) -> MediaJobStatus | None:
    if not idea_needs_media(content_idea):
        return None

    settings = get_settings()
    if not is_image_generation_allowed(settings):
        row = create_media_job(
            session,
            job_id=str(uuid.uuid4()),
            content_idea_id=content_idea.id,
            brief_item_id=brief_item_id,
            brief_id=brief_id,
            status="skipped",
            stage="Media generation is not configured",
            progress_percent=100,
            completed_at=_now(),
        )
        return media_job_to_schema(row)

    row = create_media_job(
        session,
        job_id=str(uuid.uuid4()),
        content_idea_id=content_idea.id,
        brief_item_id=brief_item_id,
        brief_id=brief_id,
        status="queued",
        stage="Waiting to start…",
        progress_percent=0,
    )
    _schedule_task(row.id)
    return media_job_to_schema(row)


def resume_pending_media_jobs() -> None:
    session = SessionLocal()
    try:
        for job in list_resumable_media_jobs(session):
            if job.status == "generating_media":
                update_media_job(
                    session,
                    job.id,
                    status="queued",
                    stage="Resuming…",
                    progress_percent=job.progress_percent,
                )
            _schedule_task(job.id)
    finally:
        session.close()
