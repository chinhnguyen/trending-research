from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

MediaJobStatusName = Literal["queued", "generating_media", "completed", "failed", "skipped"]

ACTIVE_MEDIA_JOB_STATUSES = frozenset({"queued", "generating_media"})


class MediaJobStatus(BaseModel):
    id: str
    status: MediaJobStatusName
    stage: str
    progress_percent: int = Field(ge=0, le=100)
    error_message: str | None = None
    brief_id: str | None = None
    brief_item_id: str | None = None
    content_idea_id: str | None = None
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None = None
