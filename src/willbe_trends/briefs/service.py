import json
import re
import uuid
from datetime import datetime, timezone

from willbe_trends.db.models import BriefItemRow, ResearchReportRow
from willbe_trends.models.briefs import BriefCaption, BriefItem, ContentIdea, ProductServiceTieIn, TrendBrief
from willbe_trends.models.search import WebCitation
from willbe_trends.models.trends import TrendSignal
from willbe_trends.models.usage import LLMUsageStats
from willbe_trends.llm.base import LLMProvider, LLMResponse

BRIEF_ITEM_SYSTEM_PROMPT = """You are a beauty trend strategist helping salon owners turn evidence-backed trends into a short actionable brief.
Return ONLY valid JSON with this shape:
{
  "evidence_summary": "2-3 sentences grounded in the supplied report and citations",
  "why_now": "1-2 sentences explaining timing and relevance",
  "caveats": "optional string or null",
  "angles": ["angle 1", "angle 2", "angle 3"],
  "captions": [
    {"locale": "en", "caption": "string", "cta": "optional string"}
  ],
  "hashtags": ["#tag"],
  "posting_tip": "short practical posting suggestion",
  "service_suggestion": "service or offer to promote",
  "product_suggestion": "optional retail or treatment tie-in",
  "rationale": "why the suggestion fits this trend"
}
Rules:
- Ground every claim in the provided report trend and citations.
- Do not invent statistics or unsupported sources.
- Keep suggestions practical for a salon social post.
- Captions should sound warm, concise, and human.
- Return 3-5 hashtags only."""


def _extract_json_payload(text: str) -> dict:
    stripped = text.strip()
    fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", stripped)
    candidate = fence_match.group(1).strip() if fence_match else stripped
    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        start = candidate.find("{")
        end = candidate.rfind("}")
        if start == -1 or end == -1:
            raise ValueError("Model response did not contain valid JSON.") from None
        return json.loads(candidate[start : end + 1])


def _sum_usage(parts: list[LLMUsageStats | None]) -> LLMUsageStats | None:
    present = [part for part in parts if part is not None]
    if not present:
        return None
    return LLMUsageStats(
        prompt_tokens=sum(part.prompt_tokens for part in present),
        completion_tokens=sum(part.completion_tokens for part in present),
        total_tokens=sum(part.total_tokens for part in present),
        estimated_cost_usd=sum(part.estimated_cost_usd for part in present),
    )


def _locale_candidates(region: str) -> list[str]:
    region_lower = region.lower()
    if "fin" in region_lower:
        return ["en", "fi"]
    if "viet" in region_lower:
        return ["en", "vi"]
    return ["en"]


def _brief_item_prompt(
    *,
    trend: TrendSignal,
    report_summary: str,
    citations: list[WebCitation],
    region: str,
    research_time: str,
    score: float,
    locales: list[str],
) -> str:
    citation_lines = "\n".join(
        f"- {citation.title}: {citation.snippet or citation.url}" for citation in citations[:5]
    )
    return f"""Region: {region}
Time period: {research_time}
Brief score: {score:.2f}
Locales: {", ".join(locales)}
Report summary:
{report_summary}

Trend:
- Name: {trend.name}
- Description: {trend.description}
- Popularity: {trend.popularity}
- Confidence: {trend.confidence:.2f}
- Colors: {", ".join(trend.colors) or "none"}
- Techniques: {", ".join(trend.techniques) or "none"}
- Tags: {", ".join(trend.tags) or "none"}
- Source hint: {trend.source_hint or "none"}

Supporting citations:
{citation_lines or "- No citations available"}
"""


def score_trend(trend: TrendSignal, citations: list[WebCitation]) -> float:
    confidence_score = max(0.0, min(1.0, trend.confidence))
    richness_score = min(1.0, (len(trend.colors) + len(trend.techniques) + len(trend.tags)) / 8)

    evidence_matches = 0
    needle_terms = {
        trend.name.lower(),
        *(value.lower() for value in trend.colors[:2]),
        *(value.lower() for value in trend.techniques[:2]),
        *(value.lower() for value in trend.tags[:2]),
    }
    for citation in citations:
        haystack = f"{citation.title} {citation.snippet} {citation.source_name or ''}".lower()
        if any(term and term in haystack for term in needle_terms):
            evidence_matches += 1
    evidence_score = min(1.0, 0.35 * bool(trend.source_hint) + 0.25 * min(evidence_matches, 3))

    return round(0.5 * confidence_score + 0.35 * evidence_score + 0.15 * richness_score, 4)


def _idea_from_payload(payload: dict) -> tuple[str, str, str | None, ContentIdea]:
    captions = [BriefCaption.model_validate(item) for item in payload.get("captions", [])]
    if not captions:
        captions = [BriefCaption(locale="en", caption="Show the trend with your latest salon work.")]

    idea = ContentIdea(
        id=str(uuid.uuid4()),
        angles=payload.get("angles", [])[:3],
        captions=captions,
        hashtags=payload.get("hashtags", [])[:5],
        posting_tip=payload.get("posting_tip"),
        product_mapping=(
            ProductServiceTieIn(
                service_suggestion=payload.get("service_suggestion", "").strip(),
                product_suggestion=payload.get("product_suggestion", "").strip(),
                rationale=payload.get("rationale", "").strip(),
            )
            if payload.get("service_suggestion") and payload.get("product_suggestion") and payload.get("rationale")
            else None
        ),
        generated_at=datetime.now(timezone.utc),
    )
    return (
        payload.get("evidence_summary", "Grounded in the current report and saved citations.").strip(),
        payload.get("why_now", "This trend is gaining attention right now.").strip(),
        payload.get("caveats"),
        idea,
    )


async def build_brief_item(
    *,
    llm: LLMProvider,
    trend: TrendSignal,
    report_summary: str,
    citations: list[WebCitation],
    region: str,
    research_time: str,
    rank: int,
    score: float,
    locales: list[str],
) -> tuple[BriefItem, LLMResponse]:
    response = await llm.complete(
        system=BRIEF_ITEM_SYSTEM_PROMPT,
        user=_brief_item_prompt(
            trend=trend,
            report_summary=report_summary,
            citations=citations,
            region=region,
            research_time=research_time,
            score=score,
            locales=locales,
        ),
    )
    payload = _extract_json_payload(response.content)
    evidence_summary, why_now, caveats, idea = _idea_from_payload(payload)
    item = BriefItem(
        id=str(uuid.uuid4()),
        rank=rank,
        score=score,
        evidence_summary=evidence_summary,
        why_now=why_now,
        caveats=caveats,
        trend=trend,
        content_idea=idea,
    )
    return item, response


def _trend_row_to_signal(trend) -> TrendSignal:
    return TrendSignal(
        name=trend.name,
        description=trend.description,
        popularity=trend.popularity,
        colors=json.loads(trend.colors_json),
        techniques=json.loads(trend.techniques_json),
        tags=json.loads(trend.tags_json),
        confidence=trend.confidence,
        source_hint=trend.source_hint,
        image_url=trend.image_url,
        image_source_url=trend.image_source_url,
        image_alt=trend.image_alt,
    )


def _report_citations(row: ResearchReportRow) -> list[WebCitation]:
    return [
        WebCitation(
            title=citation.title,
            url=citation.url,
            snippet=citation.snippet,
            preferred=citation.preferred,
            source_name=citation.source_name,
            query=citation.query,
        )
        for citation in row.citations
    ]


def find_trend_in_report(row: ResearchReportRow, trend_name: str):
    for trend in row.trends:
        if trend.name == trend_name:
            return trend
    lowered = trend_name.lower()
    for trend in row.trends:
        if trend.name.lower() == lowered:
            return trend
    return None


async def generate_brief_for_trend(
    *,
    row: ResearchReportRow,
    llm: LLMProvider,
    trend_name: str,
) -> TrendBrief:
    trend_row = find_trend_in_report(row, trend_name)
    if trend_row is None:
        raise ValueError(f"Trend not found in report: {trend_name}")

    citations = _report_citations(row)
    trend = _trend_row_to_signal(trend_row)
    score = score_trend(trend, citations)
    locales = _locale_candidates(row.region)
    item, response = await build_brief_item(
        llm=llm,
        trend=trend,
        report_summary=row.summary,
        citations=citations,
        region=row.region,
        research_time=row.research_time or "",
        rank=1,
        score=score,
        locales=locales,
    )
    return TrendBrief(
        id=str(uuid.uuid4()),
        report_id=row.id,
        title=f"Post brief — {trend.name}",
        summary=f"Social post ideas for {trend.name}, grounded in the saved {row.research_time or 'current'} research.",
        region=row.region,
        research_time=row.research_time or "",
        generated_at=datetime.now(timezone.utc),
        llm_provider=response.provider,
        llm_model=response.model,
        llm_usage=response.usage,
        items=[item],
    )


async def generate_brief_from_report(
    *,
    row: ResearchReportRow,
    llm: LLMProvider,
    max_trends: int = 8,
) -> TrendBrief:
    citations = _report_citations(row)
    ranked_trends = sorted(
        (
            (
                score_trend(_trend_row_to_signal(trend), citations),
                _trend_row_to_signal(trend),
            )
            for trend in row.trends
        ),
        key=lambda pair: pair[0],
        reverse=True,
    )[:max_trends]

    locales = _locale_candidates(row.region)
    items: list[BriefItem] = []
    responses: list[LLMResponse] = []
    for index, (score, trend) in enumerate(ranked_trends, start=1):
        item, response = await build_brief_item(
            llm=llm,
            trend=trend,
            report_summary=row.summary,
            citations=citations,
            region=row.region,
            research_time=row.research_time or "",
            rank=index,
            score=score,
            locales=locales,
        )
        items.append(item)
        responses.append(response)

    usage = _sum_usage([response.usage for response in responses])
    return TrendBrief(
        id=str(uuid.uuid4()),
        report_id=row.id,
        title=f"Trend brief — {row.region} — {row.research_time or 'current'}",
        summary=row.summary,
        region=row.region,
        research_time=row.research_time or "",
        generated_at=datetime.now(timezone.utc),
        llm_provider=responses[0].provider if responses else row.llm_provider,
        llm_model=responses[0].model if responses else row.llm_model,
        llm_usage=usage,
        items=items,
    )


async def regenerate_content_idea_for_item(
    *,
    llm: LLMProvider,
    item: BriefItemRow,
    report_summary: str,
    citations: list[WebCitation],
    region: str,
    research_time: str,
) -> tuple[ContentIdea, LLMResponse]:
    trend = TrendSignal(
        name=item.trend_name,
        description=item.trend_description,
        popularity=item.trend_popularity,
        colors=json.loads(item.colors_json),
        techniques=json.loads(item.techniques_json),
        tags=json.loads(item.tags_json),
        confidence=item.confidence,
        source_hint=item.source_hint,
        image_url=item.image_url,
        image_source_url=item.image_source_url,
        image_alt=item.image_alt,
    )
    response = await llm.complete(
        system=BRIEF_ITEM_SYSTEM_PROMPT,
        user=_brief_item_prompt(
            trend=trend,
            report_summary=report_summary,
            citations=citations,
            region=region,
            research_time=research_time,
            score=item.score,
            locales=_locale_candidates(region),
        ),
    )
    payload = _extract_json_payload(response.content)
    _, _, _, idea = _idea_from_payload(payload)
    return idea, response
