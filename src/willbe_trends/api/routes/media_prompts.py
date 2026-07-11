from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from willbe_trends.api.deps import get_db
from willbe_trends.api.schemas import (
    ContentIdeaOut,
    MediaJobOut,
    MediaPromptActionOut,
    MediaPromptAdjustRequest,
    MediaPromptRegenerateRequest,
    MediaPromptTargetRequest,
)
from willbe_trends.config import get_settings
from willbe_trends.db.repository import (
    _content_idea_to_schema,
    get_active_media_job_for_content_idea,
    get_brief_item,
    get_content_idea_row,
    update_content_idea,
)
from willbe_trends.llm.registry import create_provider
from willbe_trends.media.jobs import cancel_media_job, schedule_media_job_for_option
from willbe_trends.media.prompt_review import (
    accept_media_prompt,
    adjust_media_prompt,
    cancel_media_prompt,
    regenerate_option_field,
    reopen_media_prompt,
)

router = APIRouter(tags=["media-prompts"])


def _content_idea_out(
    db: Session,
    *,
    brief_item_id: str,
    idea,
    active_job=None,
) -> ContentIdeaOut:
    return ContentIdeaOut(
        brief_item_id=brief_item_id,
        active_media_job=MediaJobOut(**active_job.model_dump()) if active_job else None,
        **idea.model_dump(),
    )


def _load_idea_context(db: Session, content_idea_id: str):
    idea_row = get_content_idea_row(db, content_idea_id)
    if idea_row is None:
        raise HTTPException(status_code=404, detail="Content idea not found")
    item = get_brief_item(db, idea_row.brief_item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Brief item not found")
    idea = _content_idea_to_schema(idea_row)
    if idea is None:
        raise HTTPException(status_code=500, detail="Content idea could not be loaded")
    return item, idea


@router.patch("/media-prompts", response_model=MediaPromptActionOut)
def adjust_prompt(request: MediaPromptAdjustRequest, db: Session = Depends(get_db)):
    item, idea = _load_idea_context(db, request.content_idea_id)
    try:
        updated = adjust_media_prompt(
            idea,
            kind=request.kind,
            sequence=request.sequence,
            prompt=request.prompt,
            hook=request.hook,
            caption=request.caption,
            hashtags=request.hashtags,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    row = update_content_idea(db, idea.id, updated)
    saved = _content_idea_to_schema(row)
    if saved is None:
        raise HTTPException(status_code=500, detail="Content idea could not be saved")
    return _content_idea_out(db, brief_item_id=item.id, idea=saved)


@router.post("/media-prompts/accept", response_model=MediaPromptActionOut)
def accept_prompt(request: MediaPromptTargetRequest, db: Session = Depends(get_db)):
    item, idea = _load_idea_context(db, request.content_idea_id)
    try:
        updated = accept_media_prompt(idea, kind=request.kind, sequence=request.sequence)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    row = update_content_idea(db, idea.id, updated)
    saved = _content_idea_to_schema(row)
    if saved is None:
        raise HTTPException(status_code=500, detail="Content idea could not be saved")
    active_job = schedule_media_job_for_option(
        db,
        content_idea=saved,
        brief_item_id=item.id,
        brief_id=item.brief_id,
        target_kind=request.kind,
        target_sequence=request.sequence,
    )
    return _content_idea_out(db, brief_item_id=item.id, idea=saved, active_job=active_job)


@router.post("/media-prompts/regenerate", response_model=MediaPromptActionOut)
async def regenerate_prompt(request: MediaPromptRegenerateRequest, db: Session = Depends(get_db)):
    item, idea = _load_idea_context(db, request.content_idea_id)
    settings = get_settings()
    llm = create_provider(None, settings=settings)
    try:
        updated = await regenerate_option_field(
            llm=llm,
            idea=idea,
            kind=request.kind,
            sequence=request.sequence,
            field=request.field,
            trend_name=item.trend_name,
            trend_description=item.trend_description,
            region=item.brief.report.region,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    row = update_content_idea(db, idea.id, updated)
    saved = _content_idea_to_schema(row)
    if saved is None:
        raise HTTPException(status_code=500, detail="Content idea could not be saved")
    return _content_idea_out(db, brief_item_id=item.id, idea=saved)


@router.post("/media-prompts/cancel", response_model=MediaPromptActionOut)
def cancel_prompt(request: MediaPromptTargetRequest, db: Session = Depends(get_db)):
    item, idea = _load_idea_context(db, request.content_idea_id)
    active = get_active_media_job_for_content_idea(db, idea.id)
    if (
        active is not None
        and active.target_kind == request.kind
        and active.target_sequence == request.sequence
    ):
        cancel_media_job(db, active.id)
        idea_row = get_content_idea_row(db, idea.id)
        saved = _content_idea_to_schema(idea_row)
        if saved is None:
            raise HTTPException(status_code=500, detail="Content idea could not be loaded")
        return _content_idea_out(db, brief_item_id=item.id, idea=saved)

    try:
        updated = cancel_media_prompt(idea, kind=request.kind, sequence=request.sequence)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    row = update_content_idea(db, idea.id, updated)
    saved = _content_idea_to_schema(row)
    if saved is None:
        raise HTTPException(status_code=500, detail="Content idea could not be saved")
    return _content_idea_out(db, brief_item_id=item.id, idea=saved)


@router.post("/media-prompts/reopen", response_model=MediaPromptActionOut)
def reopen_prompt(request: MediaPromptTargetRequest, db: Session = Depends(get_db)):
    item, idea = _load_idea_context(db, request.content_idea_id)
    try:
        updated = reopen_media_prompt(idea, kind=request.kind, sequence=request.sequence)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    row = update_content_idea(db, idea.id, updated)
    saved = _content_idea_to_schema(row)
    if saved is None:
        raise HTTPException(status_code=500, detail="Content idea could not be saved")
    return _content_idea_out(db, brief_item_id=item.id, idea=saved)
