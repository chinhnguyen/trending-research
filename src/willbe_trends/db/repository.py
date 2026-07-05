import uuid
from datetime import datetime

from sqlalchemy.orm import Session, joinedload

from willbe_trends.db.models import (
    ResearchReportRow,
    TrendSignalRow,
    WebCitationRow,
    dumps_json,
    loads_json,
)
from willbe_trends.models.preferences import UserPreferences
from willbe_trends.models.search import WebCitation, WebResearchBundle
from willbe_trends.models.trends import TrendCategory, TrendReport, TrendSignal
from willbe_trends.models.usage import LLMUsageStats


def report_to_schema(row: ResearchReportRow) -> TrendReport:
    web_bundle = None
    if row.web_search_provider:
        web_bundle = WebResearchBundle(
            enabled=row.web_search_enabled,
            search_provider=row.web_search_provider,
            queries=loads_json(row.web_queries_json, []),
            citations=[
                WebCitation(
                    title=c.title,
                    url=c.url,
                    snippet=c.snippet,
                    preferred=c.preferred,
                    source_name=c.source_name,
                    query=c.query,
                )
                for c in row.citations
            ],
        )

    usage = None
    if row.llm_total_tokens or row.llm_estimated_cost_usd:
        usage = LLMUsageStats(
            prompt_tokens=row.llm_prompt_tokens,
            completion_tokens=row.llm_completion_tokens,
            total_tokens=row.llm_total_tokens,
            estimated_cost_usd=row.llm_estimated_cost_usd,
        )

    return TrendReport(
        category=TrendCategory(row.category),
        mode=row.mode,
        research_time=row.research_time or "",
        summary=row.summary,
        trends=[
            TrendSignal(
                name=t.name,
                description=t.description,
                popularity=t.popularity,
                colors=loads_json(t.colors_json, []),
                techniques=loads_json(t.techniques_json, []),
                tags=loads_json(t.tags_json, []),
                confidence=t.confidence,
                source_hint=t.source_hint,
                image_url=t.image_url,
                image_source_url=t.image_source_url,
                image_alt=t.image_alt,
            )
            for t in row.trends
        ],
        generated_at=row.generated_at.isoformat(),
        llm_provider=row.llm_provider,
        llm_model=row.llm_model,
        llm_usage=usage,
        web_research=web_bundle,
    )


def save_report(
    session: Session,
    report: TrendReport,
    *,
    region: str = "global",
    web_search_enabled: bool = True,
    preferences: UserPreferences | None = None,
) -> ResearchReportRow:
    report_id = str(uuid.uuid4())
    generated_at = datetime.fromisoformat(report.generated_at.replace("Z", "+00:00"))

    usage = report.llm_usage or LLMUsageStats()

    row = ResearchReportRow(
        id=report_id,
        category=report.category.value,
        mode=report.mode,
        summary=report.summary,
        region=region,
        research_time=report.research_time,
        generated_at=generated_at,
        llm_provider=report.llm_provider,
        llm_model=report.llm_model,
        llm_prompt_tokens=usage.prompt_tokens,
        llm_completion_tokens=usage.completion_tokens,
        llm_total_tokens=usage.total_tokens,
        llm_estimated_cost_usd=usage.estimated_cost_usd,
        web_search_enabled=web_search_enabled,
        web_search_provider=report.web_research.search_provider if report.web_research else None,
        web_queries_json=dumps_json(report.web_research.queries if report.web_research else []),
        preferences_json=preferences.model_dump_json() if preferences else None,
    )

    for index, trend in enumerate(report.trends):
        row.trends.append(
            TrendSignalRow(
                position=index,
                name=trend.name,
                description=trend.description,
                popularity=trend.popularity,
                colors_json=dumps_json(trend.colors),
                techniques_json=dumps_json(trend.techniques),
                tags_json=dumps_json(trend.tags),
                confidence=trend.confidence,
                source_hint=trend.source_hint,
                image_url=trend.image_url,
                image_source_url=trend.image_source_url,
                image_alt=trend.image_alt,
            )
        )

    if report.web_research:
        for index, citation in enumerate(report.web_research.citations):
            row.citations.append(
                WebCitationRow(
                    position=index,
                    title=citation.title,
                    url=citation.url,
                    snippet=citation.snippet,
                    preferred=citation.preferred,
                    source_name=citation.source_name,
                    query=citation.query,
                )
            )

    session.add(row)
    session.commit()
    session.refresh(row)
    return row


def list_reports(session: Session, *, limit: int = 50, offset: int = 0) -> list[ResearchReportRow]:
    return (
        session.query(ResearchReportRow)
        .options(joinedload(ResearchReportRow.trends), joinedload(ResearchReportRow.citations))
        .order_by(ResearchReportRow.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )


def get_report(session: Session, report_id: str) -> ResearchReportRow | None:
    return (
        session.query(ResearchReportRow)
        .options(joinedload(ResearchReportRow.trends), joinedload(ResearchReportRow.citations))
        .filter(ResearchReportRow.id == report_id)
        .one_or_none()
    )
