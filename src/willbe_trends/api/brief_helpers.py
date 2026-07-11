from sqlalchemy.orm import Session

from willbe_trends.api.schemas import BriefOut, MediaJobOut
from willbe_trends.db.models import ResearchBriefRow
from willbe_trends.db.repository import (
    brief_to_schema,
    get_active_media_jobs_for_brief,
    media_job_to_schema,
)


def build_brief_out(session: Session, row: ResearchBriefRow) -> BriefOut:
    brief = brief_to_schema(row)
    jobs = get_active_media_jobs_for_brief(session, row.id)
    return BriefOut(
        **brief.model_dump(),
        active_media_jobs=[MediaJobOut(**media_job_to_schema(job).model_dump()) for job in jobs],
    )
