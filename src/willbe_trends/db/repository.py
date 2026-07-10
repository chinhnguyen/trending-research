import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session, joinedload

from willbe_trends.db.models import (
    BriefItemRow,
    ContentIdeaRow,
    MediaGenerationJobRow,
    ResearchReportRow,
    ResearchBriefRow,
    TrendSignalRow,
    WebCitationRow,
    dumps_json,
    loads_json,
)
from willbe_trends.models.briefs import (
    BriefCaption,
    BriefItem,
    ContentIdea,
    ImageRecommendation,
    PlatformPostReview,
    ProductServiceTieIn,
    ShortVideoRecommendation,
    TrendBrief,
    VideoRecommendation,
)
from willbe_trends.models.preferences import UserPreferences
from willbe_trends.models.search import WebCitation, WebResearchBundle
from willbe_trends.models.trends import TrendCategory, TrendReport, TrendSignal
from willbe_trends.models.usage import LLMUsageStats
from willbe_trends.models.media_jobs import ACTIVE_MEDIA_JOB_STATUSES, MediaJobStatus


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


def latest_content_idea_row(item: BriefItemRow) -> ContentIdeaRow | None:
    if not item.ideas:
        return None
    return max(item.ideas, key=lambda row: row.created_at)


def _content_idea_to_schema(row: ContentIdeaRow | None) -> ContentIdea | None:
    if row is None:
        return None

    platform_review_raw = loads_json(row.platform_review_json, {})
    platform_review = (
        PlatformPostReview.model_validate(platform_review_raw)
        if platform_review_raw
        else None
    )
    video_raw = loads_json(row.video_recommendation_json, None) if row.video_recommendation_json else None

    return ContentIdea(
        id=row.id,
        platform=row.platform or "instagram",
        post_format=row.post_format or "image",
        angles=loads_json(row.angles_json, []),
        captions=[BriefCaption.model_validate(item) for item in loads_json(row.captions_json, [])],
        hashtags=loads_json(row.hashtags_json, []),
        posting_tip=row.posting_tip,
        product_mapping=(
            ProductServiceTieIn(
                service_suggestion=row.service_suggestion or "",
                product_suggestion=row.product_suggestion or "",
                rationale=row.rationale or "",
            )
            if row.service_suggestion and row.product_suggestion and row.rationale
            else None
        ),
        platform_review=platform_review,
        image_recommendations=[
            ImageRecommendation.model_validate(item)
            for item in loads_json(row.image_recommendations_json, [])
        ],
        video_recommendations=[
            ShortVideoRecommendation.model_validate(item)
            for item in loads_json(row.video_recommendations_json, [])
        ],
        video_recommendation=VideoRecommendation.model_validate(video_raw) if video_raw else None,
        generated_at=row.created_at,
    )


def _content_idea_row_from_schema(idea: ContentIdea, brief_item_id: str) -> ContentIdeaRow:
    return ContentIdeaRow(
        id=idea.id,
        brief_item_id=brief_item_id,
        angles_json=dumps_json(idea.angles),
        captions_json=dumps_json([caption.model_dump() for caption in idea.captions]),
        hashtags_json=dumps_json(idea.hashtags),
        posting_tip=idea.posting_tip,
        service_suggestion=idea.product_mapping.service_suggestion if idea.product_mapping else None,
        product_suggestion=idea.product_mapping.product_suggestion if idea.product_mapping else None,
        rationale=idea.product_mapping.rationale if idea.product_mapping else None,
        platform=idea.platform,
        post_format=idea.post_format,
        platform_review_json=dumps_json(idea.platform_review.model_dump() if idea.platform_review else {}),
        image_recommendations_json=dumps_json(
            [item.model_dump() for item in idea.image_recommendations]
        ),
        video_recommendations_json=dumps_json(
            [item.model_dump() for item in idea.video_recommendations]
        ),
        video_recommendation_json=(
            dumps_json(idea.video_recommendation.model_dump()) if idea.video_recommendation else None
        ),
        created_at=idea.generated_at,
    )


def brief_to_schema(row: ResearchBriefRow) -> TrendBrief:
    usage = None
    if row.llm_total_tokens or row.llm_estimated_cost_usd:
        usage = LLMUsageStats(
            prompt_tokens=row.llm_prompt_tokens,
            completion_tokens=row.llm_completion_tokens,
            total_tokens=row.llm_total_tokens,
            estimated_cost_usd=row.llm_estimated_cost_usd,
        )

    return TrendBrief(
        id=row.id,
        report_id=row.report_id,
        title=row.title,
        summary=row.summary,
        region=row.region,
        research_time=row.research_time,
        generated_at=row.created_at,
        llm_provider=row.llm_provider,
        llm_model=row.llm_model,
        llm_usage=usage,
        items=[
            BriefItem(
                id=item.id,
                rank=item.rank,
                score=item.score,
                evidence_summary=item.evidence_summary,
                why_now=item.why_now,
                caveats=item.caveats,
                trend=TrendSignal(
                    name=item.trend_name,
                    description=item.trend_description,
                    popularity=item.trend_popularity,
                    colors=loads_json(item.colors_json, []),
                    techniques=loads_json(item.techniques_json, []),
                    tags=loads_json(item.tags_json, []),
                    confidence=item.confidence,
                    source_hint=item.source_hint,
                    image_url=item.image_url,
                    image_source_url=item.image_source_url,
                    image_alt=item.image_alt,
                ),
                content_idea=_content_idea_to_schema(latest_content_idea_row(item)),
            )
            for item in row.items
        ],
    )


def save_brief(session: Session, brief: TrendBrief) -> ResearchBriefRow:
    usage = brief.llm_usage or LLMUsageStats()
    row = ResearchBriefRow(
        id=brief.id,
        report_id=brief.report_id,
        title=brief.title,
        summary=brief.summary,
        region=brief.region,
        research_time=brief.research_time,
        llm_provider=brief.llm_provider,
        llm_model=brief.llm_model,
        llm_prompt_tokens=usage.prompt_tokens,
        llm_completion_tokens=usage.completion_tokens,
        llm_total_tokens=usage.total_tokens,
        llm_estimated_cost_usd=usage.estimated_cost_usd,
        created_at=brief.generated_at,
    )
    for item in brief.items:
        item_row = BriefItemRow(
            id=item.id,
            rank=item.rank,
            score=item.score,
            trend_name=item.trend.name,
            trend_description=item.trend.description,
            trend_popularity=item.trend.popularity,
            colors_json=dumps_json(item.trend.colors),
            techniques_json=dumps_json(item.trend.techniques),
            tags_json=dumps_json(item.trend.tags),
            confidence=item.trend.confidence,
            source_hint=item.trend.source_hint,
            image_url=item.trend.image_url,
            image_source_url=item.trend.image_source_url,
            image_alt=item.trend.image_alt,
            evidence_summary=item.evidence_summary,
            why_now=item.why_now,
            caveats=item.caveats,
        )
        if item.content_idea:
            item_row.ideas.append(_content_idea_row_from_schema(item.content_idea, item.id))
        row.items.append(item_row)

    session.add(row)
    session.commit()
    session.refresh(row)
    return row


def get_brief(session: Session, brief_id: str) -> ResearchBriefRow | None:
    return (
        session.query(ResearchBriefRow)
        .options(joinedload(ResearchBriefRow.items).joinedload(BriefItemRow.ideas))
        .filter(ResearchBriefRow.id == brief_id)
        .one_or_none()
    )


def get_latest_brief_for_report(session: Session, report_id: str) -> ResearchBriefRow | None:
    return (
        session.query(ResearchBriefRow)
        .options(joinedload(ResearchBriefRow.items).joinedload(BriefItemRow.ideas))
        .filter(ResearchBriefRow.report_id == report_id)
        .order_by(ResearchBriefRow.created_at.desc())
        .first()
    )


def get_brief_item(session: Session, brief_item_id: str) -> BriefItemRow | None:
    return (
        session.query(BriefItemRow)
        .options(joinedload(BriefItemRow.ideas), joinedload(BriefItemRow.brief))
        .filter(BriefItemRow.id == brief_item_id)
        .one_or_none()
    )


def replace_content_idea(
    session: Session,
    brief_item_id: str,
    idea: ContentIdea,
) -> ContentIdeaRow:
    item = get_brief_item(session, brief_item_id)
    if item is None:
        raise ValueError("Brief item not found")

    row = _content_idea_row_from_schema(idea, brief_item_id)
    session.add(row)
    session.commit()
    session.refresh(row)
    return row


def get_content_idea_row(session: Session, idea_id: str) -> ContentIdeaRow | None:
    return session.get(ContentIdeaRow, idea_id)


def update_content_idea(session: Session, idea_id: str, idea: ContentIdea) -> ContentIdeaRow:
    row = get_content_idea_row(session, idea_id)
    if row is None:
        raise ValueError("Content idea not found")

    updated = _content_idea_row_from_schema(idea, row.brief_item_id)
    row.angles_json = updated.angles_json
    row.captions_json = updated.captions_json
    row.hashtags_json = updated.hashtags_json
    row.posting_tip = updated.posting_tip
    row.service_suggestion = updated.service_suggestion
    row.product_suggestion = updated.product_suggestion
    row.rationale = updated.rationale
    row.platform = updated.platform
    row.post_format = updated.post_format
    row.platform_review_json = updated.platform_review_json
    row.image_recommendations_json = updated.image_recommendations_json
    row.video_recommendations_json = updated.video_recommendations_json
    row.video_recommendation_json = updated.video_recommendation_json
    session.commit()
    session.refresh(row)
    return row


def idea_needs_media(idea: ContentIdea) -> bool:
    if idea.post_format == "video":
        return any(not video.generated_url for video in idea.video_recommendations)
    return any(not image.generated_url for image in idea.image_recommendations)


def media_job_to_schema(row: MediaGenerationJobRow) -> MediaJobStatus:
    return MediaJobStatus(
        id=row.id,
        status=row.status,
        stage=row.stage,
        progress_percent=row.progress_percent,
        error_message=row.error_message,
        brief_id=row.brief_id,
        brief_item_id=row.brief_item_id,
        content_idea_id=row.content_idea_id,
        created_at=row.created_at,
        updated_at=row.updated_at,
        completed_at=row.completed_at,
    )


def create_media_job(
    session: Session,
    *,
    job_id: str,
    content_idea_id: str,
    brief_item_id: str,
    brief_id: str,
    status: str,
    stage: str,
    progress_percent: int,
    error_message: str | None = None,
    completed_at: datetime | None = None,
) -> MediaGenerationJobRow:
    now = datetime.now(timezone.utc)
    row = MediaGenerationJobRow(
        id=job_id,
        content_idea_id=content_idea_id,
        brief_item_id=brief_item_id,
        brief_id=brief_id,
        status=status,
        stage=stage,
        progress_percent=progress_percent,
        error_message=error_message,
        created_at=now,
        updated_at=now,
        completed_at=completed_at,
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    return row


def update_media_job(
    session: Session,
    job_id: str,
    *,
    status: str | None = None,
    stage: str | None = None,
    progress_percent: int | None = None,
    error_message: str | None = None,
    completed_at: datetime | None = None,
) -> MediaGenerationJobRow | None:
    row = get_media_job(session, job_id)
    if row is None:
        return None
    if status is not None:
        row.status = status
    if stage is not None:
        row.stage = stage
    if progress_percent is not None:
        row.progress_percent = progress_percent
    if error_message is not None:
        row.error_message = error_message
    if completed_at is not None:
        row.completed_at = completed_at
    row.updated_at = datetime.now(timezone.utc)
    session.commit()
    session.refresh(row)
    return row


def get_media_job(session: Session, job_id: str) -> MediaGenerationJobRow | None:
    return session.get(MediaGenerationJobRow, job_id)


def get_active_media_jobs_for_brief(session: Session, brief_id: str) -> list[MediaGenerationJobRow]:
    return (
        session.query(MediaGenerationJobRow)
        .filter(
            MediaGenerationJobRow.brief_id == brief_id,
            MediaGenerationJobRow.status.in_(ACTIVE_MEDIA_JOB_STATUSES),
        )
        .order_by(MediaGenerationJobRow.created_at.desc())
        .all()
    )


def get_active_media_job_for_content_idea(
    session: Session,
    content_idea_id: str,
) -> MediaGenerationJobRow | None:
    return (
        session.query(MediaGenerationJobRow)
        .filter(
            MediaGenerationJobRow.content_idea_id == content_idea_id,
            MediaGenerationJobRow.status.in_(ACTIVE_MEDIA_JOB_STATUSES),
        )
        .order_by(MediaGenerationJobRow.created_at.desc())
        .first()
    )


def list_resumable_media_jobs(session: Session) -> list[MediaGenerationJobRow]:
    return (
        session.query(MediaGenerationJobRow)
        .filter(MediaGenerationJobRow.status.in_(ACTIVE_MEDIA_JOB_STATUSES))
        .order_by(MediaGenerationJobRow.created_at.asc())
        .all()
    )
