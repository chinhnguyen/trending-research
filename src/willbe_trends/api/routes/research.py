from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from willbe_trends.models.category import TrendCategory
from willbe_trends.api.deps import get_db
from willbe_trends.api.schemas import (
    PersonalizedResearchRequest,
    ResearchDetail,
    ResearchListItem,
    ResearchListResponse,
    ResearchRunRequest,
)
from willbe_trends.config import get_settings
from willbe_trends.db.models import ResearchReportRow
from willbe_trends.db.repository import get_report, list_reports, report_to_schema, save_report
from willbe_trends.models.usage import LLMUsageStats
from willbe_trends.llm.registry import create_provider
from willbe_trends.research.neutral import research_neutral_trends
from willbe_trends.research.personalized import research_personalized_trends

router = APIRouter(tags=["research"])


def _resolve_settings(request: ResearchRunRequest):
    settings = get_settings()
    updates = {}
    if request.provider:
        updates["willbe_llm_provider"] = request.provider
    if request.search_provider:
        updates["willbe_search_provider"] = request.search_provider
    if updates:
        settings = settings.model_copy(update=updates)
    return settings


def _usage_from_row(row: ResearchReportRow) -> LLMUsageStats | None:
    if not row.llm_total_tokens and not row.llm_estimated_cost_usd:
        return None
    return LLMUsageStats(
        prompt_tokens=row.llm_prompt_tokens,
        completion_tokens=row.llm_completion_tokens,
        total_tokens=row.llm_total_tokens,
        estimated_cost_usd=row.llm_estimated_cost_usd,
    )


def _row_to_list_item(row: ResearchReportRow) -> ResearchListItem:
    cover_image_url = next((t.image_url for t in row.trends if t.image_url), None)
    image_count = sum(1 for t in row.trends if t.image_url)
    return ResearchListItem(
        id=row.id,
        category=TrendCategory(row.category),
        mode=row.mode,  # type: ignore[arg-type]
        summary=row.summary,
        region=row.region,
        research_time=row.research_time or "",
        generated_at=row.generated_at,
        llm_provider=row.llm_provider,
        llm_model=row.llm_model,
        llm_usage=_usage_from_row(row),
        web_search_enabled=row.web_search_enabled,
        trend_count=len(row.trends),
        citation_count=len(row.citations),
        image_count=image_count,
        cover_image_url=cover_image_url,
        created_at=row.created_at,
    )


@router.get("/health")
def health():
    return {"status": "ok"}


@router.get("/research", response_model=ResearchListResponse)
def research_list(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    rows = list_reports(db, limit=limit, offset=offset)
    total = db.query(ResearchReportRow).count()
    return ResearchListResponse(
        items=[_row_to_list_item(row) for row in rows],
        total=total,
    )


@router.get("/research/{report_id}", response_model=ResearchDetail)
def research_detail(report_id: str, db: Session = Depends(get_db)):
    row = get_report(db, report_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Research report not found")

    preferences = None
    if row.preferences_json:
        from willbe_trends.models.preferences import UserPreferences

        preferences = UserPreferences.model_validate_json(row.preferences_json)

    return ResearchDetail(
        id=row.id,
        region=row.region,
        research_time=row.research_time or "",
        web_search_enabled=row.web_search_enabled,
        preferences=preferences,
        report=report_to_schema(row),
    )


@router.post("/research/neutral", response_model=ResearchDetail)
async def run_neutral_research(
    request: ResearchRunRequest,
    db: Session = Depends(get_db),
):
    settings = _resolve_settings(request)
    llm = create_provider(request.provider, settings=settings)
    report = await research_neutral_trends(
        category=request.category,
        llm=llm,
        region=request.region,
        research_time=request.research_time,
        web_search=request.web_search,
        preferred_locale=request.preferred_locale,
        settings=settings,
    )
    row = save_report(
        db,
        report,
        region=request.region,
        web_search_enabled=request.web_search,
    )
    return ResearchDetail(
        id=row.id,
        region=row.region,
        research_time=row.research_time or report.research_time,
        web_search_enabled=row.web_search_enabled,
        preferences=None,
        report=report,
    )


@router.post("/research/personalized", response_model=ResearchDetail)
async def run_personalized_research(
    request: PersonalizedResearchRequest,
    db: Session = Depends(get_db),
):
    settings = _resolve_settings(request)
    llm = create_provider(request.provider, settings=settings)
    report = await research_personalized_trends(
        category=request.category,
        preferences=request.preferences,
        llm=llm,
        region=request.region,
        research_time=request.research_time,
        web_search=request.web_search,
        preferred_locale=request.preferred_locale,
        settings=settings,
    )
    row = save_report(
        db,
        report,
        region=request.region,
        web_search_enabled=request.web_search,
        preferences=request.preferences,
    )
    return ResearchDetail(
        id=row.id,
        region=row.region,
        research_time=row.research_time or report.research_time,
        web_search_enabled=row.web_search_enabled,
        preferences=request.preferences,
        report=report,
    )
