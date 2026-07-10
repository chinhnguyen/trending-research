from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from willbe_trends.api.deps import get_db
from willbe_trends.api.schemas import BriefGenerateRequest, BriefOut, ContentIdeaGenerateRequest, ContentIdeaOut
from willbe_trends.briefs.service import generate_brief_for_trend, generate_brief_from_report, regenerate_content_idea_for_item
from willbe_trends.config import get_settings
from willbe_trends.db.repository import (
    _content_idea_to_schema,
    brief_to_schema,
    get_brief,
    get_brief_item,
    get_latest_brief_for_report,
    get_report,
    latest_content_idea_row,
    replace_content_idea,
    save_brief,
)
from willbe_trends.llm.registry import create_provider
from willbe_trends.models.search import WebCitation

router = APIRouter(tags=["briefs"])


@router.post("/briefs/generate", response_model=BriefOut)
async def generate_brief(
    request: BriefGenerateRequest,
    db: Session = Depends(get_db),
):
    row = get_report(db, request.report_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Research report not found")

    settings = get_settings()
    llm = create_provider(request.provider, settings=settings)
    if request.trend_name:
        try:
            brief = await generate_brief_for_trend(
                row=row,
                llm=llm,
                trend_name=request.trend_name,
                platform=request.platform,
                settings=settings,
            )
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
    else:
        brief = await generate_brief_from_report(
            row=row,
            llm=llm,
            max_trends=request.max_trends,
            platform=request.platform,
            settings=settings,
        )
    saved = save_brief(db, brief)
    return brief_to_schema(saved)


@router.get("/briefs/latest", response_model=BriefOut)
def latest_brief(report_id: str = Query(...), db: Session = Depends(get_db)):
    row = get_latest_brief_for_report(db, report_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Brief not found")
    return brief_to_schema(row)


@router.get("/briefs/{brief_id}", response_model=BriefOut)
def brief_detail(brief_id: str, db: Session = Depends(get_db)):
    row = get_brief(db, brief_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Brief not found")
    return brief_to_schema(row)


@router.post("/ideas/generate", response_model=ContentIdeaOut)
async def generate_content_idea(
    request: ContentIdeaGenerateRequest,
    db: Session = Depends(get_db),
):
    item = get_brief_item(db, request.brief_item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Brief item not found")
    report = item.brief.report
    settings = get_settings()
    llm = create_provider(request.provider, settings=settings)
    prior = _content_idea_to_schema(latest_content_idea_row(item))
    idea, _response = await regenerate_content_idea_for_item(
        llm=llm,
        item=item,
        report_summary=report.summary,
        citations=[
            WebCitation(
                title=citation.title,
                url=citation.url,
                snippet=citation.snippet,
                preferred=citation.preferred,
                source_name=citation.source_name,
                query=citation.query,
            )
            for citation in report.citations
        ],
        region=report.region,
        research_time=report.research_time or "",
        platform=request.platform,
        settings=settings,
        prior_idea=prior,
    )
    row = replace_content_idea(db, request.brief_item_id, idea)
    content_idea = _content_idea_to_schema(row)
    if content_idea is None:
        raise HTTPException(status_code=500, detail="Content idea could not be created")
    return ContentIdeaOut(brief_item_id=request.brief_item_id, **content_idea.model_dump())
