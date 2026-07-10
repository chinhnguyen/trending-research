from sqlalchemy.orm import Session

from willbe_trends.api.schemas import BriefOut, MediaJobOut
from willbe_trends.db.models import ResearchBriefRow
from willbe_trends.db.repository import (
    _content_idea_to_schema,
    brief_to_schema,
    get_active_media_jobs_for_brief,
    latest_content_idea_row,
    media_job_to_schema,
)
from willbe_trends.media.jobs import schedule_media_job_for_idea


def build_brief_out(session: Session, row: ResearchBriefRow) -> BriefOut:
    brief = brief_to_schema(row)
    jobs = get_active_media_jobs_for_brief(session, row.id)
    return BriefOut(
        **brief.model_dump(),
        active_media_jobs=[MediaJobOut(**media_job_to_schema(job).model_dump()) for job in jobs],
    )


def schedule_media_jobs_for_brief(session: Session, row: ResearchBriefRow) -> None:
    for item in row.items:
        idea_row = latest_content_idea_row(item)
        if idea_row is None:
            continue
        idea = _content_idea_to_schema(idea_row)
        if idea is None:
            continue
        schedule_media_job_for_idea(
            session,
            content_idea=idea,
            brief_item_id=item.id,
            brief_id=row.id,
        )
