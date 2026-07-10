from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from willbe_trends.api.deps import get_db
from willbe_trends.api.schemas import MediaJobOut
from willbe_trends.db.repository import get_media_job, media_job_to_schema

router = APIRouter(tags=["media-jobs"])


@router.get("/media-jobs/{job_id}", response_model=MediaJobOut)
def media_job_detail(job_id: str, db: Session = Depends(get_db)):
    row = get_media_job(db, job_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Media job not found")
    return media_job_to_schema(row)
