import json
import re
import uuid
from datetime import datetime, timezone

from willbe_trends.briefs.prompts import platform_brief_system_prompt
from willbe_trends.config import Settings, get_settings
from willbe_trends.db.models import BriefItemRow, ResearchReportRow
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
    VideoScene,
)
from willbe_trends.models.search import WebCitation
from willbe_trends.models.social import PostFormat, SocialPlatform
from willbe_trends.models.trends import TrendSignal
from willbe_trends.models.usage import LLMUsageStats
from willbe_trends.llm.base import LLMProvider, LLMResponse

BRIEF_ITEM_SYSTEM_PROMPT = platform_brief_system_prompt("instagram", "image")
MAX_TOTAL_POST_OPTIONS = 6


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
    platform: SocialPlatform,
    post_format: PostFormat = "image",
    regenerate_context: str = "",
) -> str:
    citation_lines = "\n".join(
        f"- {citation.title}: {citation.snippet or citation.url}" for citation in citations[:5]
    )
    return f"""Target platform: {platform}
Post format: {post_format}
Region: {region}
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
{regenerate_context}
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


def _platform_review_from_payload(payload: dict, platform: SocialPlatform) -> PlatformPostReview:
    review = payload.get("platform_review") or {}
    captions = payload.get("captions", [])
    fallback_caption = captions[0].get("caption", "") if captions else ""
    default_format = "tiktok_video" if platform == "tiktok" else "instagram_feed"
    return PlatformPostReview(
        platform=platform,
        content_format=review.get("content_format", default_format),
        strengths=review.get("strengths", [])[:4],
        improvements=review.get("improvements", [])[:4],
        hook=review.get("hook", fallback_caption[:120] or "Lead with your best nail close-up."),
        caption=review.get("caption", fallback_caption),
        hashtags=(review.get("hashtags") or payload.get("hashtags", []))[:10],
        posting_checklist=review.get("posting_checklist", [])[:6],
        sound_strategy=review.get("sound_strategy"),
        cover_tip=review.get("cover_tip"),
    )


def _image_recommendations_from_payload(
    payload: dict,
    platform_review: PlatformPostReview | None = None,
) -> list[ImageRecommendation]:
    items = payload.get("image_recommendations", [])[:1]
    if not items:
        return []

    item = items[0]
    return [
        ImageRecommendation(
            label=item.get("label", "Post option"),
            aspect_ratio=item.get("aspect_ratio", "1:1"),
            prompt=item.get("prompt", ""),
            hook=item.get("hook") or (platform_review.hook if platform_review else None),
            caption=item.get("caption") or (platform_review.caption if platform_review else None),
            hashtags=(item.get("hashtags") or (platform_review.hashtags if platform_review else []))[:10],
        )
    ]


def _video_recommendations_from_payload(
    payload: dict,
    platform_review: PlatformPostReview | None = None,
) -> list[ShortVideoRecommendation]:
    items = payload.get("video_recommendations", [])[:1]
    if not items:
        return []

    item = items[0]
    scenes = [VideoScene.model_validate(scene) for scene in item.get("scenes", [])]
    return [
        ShortVideoRecommendation(
            label=item.get("label", "Video option"),
            aspect_ratio=item.get("aspect_ratio", "9:16"),
            prompt=item.get("prompt", ""),
            duration_seconds=int(item.get("duration_seconds", 8)),
            hook=item.get("hook") or (platform_review.hook if platform_review else None),
            caption=item.get("caption") or (platform_review.caption if platform_review else None),
            hashtags=(item.get("hashtags") or (platform_review.hashtags if platform_review else []))[:10],
            scenes=scenes,
        )
    ]


def _sync_platform_review_from_latest_option(idea: ContentIdea) -> ContentIdea:
    if idea.platform_review is None:
        return idea

    if idea.post_format == "video" and idea.video_recommendations:
        latest = idea.video_recommendations[-1]
    elif idea.image_recommendations:
        latest = idea.image_recommendations[-1]
    else:
        return idea

    return idea.model_copy(
        update={
            "platform_review": idea.platform_review.model_copy(
                update={
                    "hook": latest.hook or idea.platform_review.hook,
                    "caption": latest.caption or idea.platform_review.caption,
                    "hashtags": latest.hashtags or idea.platform_review.hashtags,
                }
            )
        }
    )


def _post_option_key(image: ImageRecommendation) -> str:
    return "|".join(
        [
            (image.hook or "").strip().lower(),
            (image.caption or "").strip().lower(),
            image.prompt.strip().lower(),
        ]
    )


def _video_option_key(video: ShortVideoRecommendation) -> str:
    return "|".join(
        [
            (video.hook or "").strip().lower(),
            (video.caption or "").strip().lower(),
            video.prompt.strip().lower(),
        ]
    )


def _video_recommendation_from_payload(payload: dict) -> VideoRecommendation | None:
    raw = payload.get("video_recommendation")
    if not raw:
        return None
    return VideoRecommendation.model_validate(raw)


def _idea_from_payload(
    payload: dict,
    *,
    platform: SocialPlatform,
    post_format: PostFormat = "image",
) -> tuple[str, str, str | None, ContentIdea]:
    captions = [BriefCaption.model_validate(item) for item in payload.get("captions", [])]
    if not captions:
        captions = [BriefCaption(locale="en", caption="Show the trend with your latest salon work.")]

    platform_review = _platform_review_from_payload(payload, platform)
    idea = ContentIdea(
        id=str(uuid.uuid4()),
        platform=platform,
        post_format=post_format,
        angles=payload.get("angles", [])[:3],
        captions=captions,
        hashtags=payload.get("hashtags", [])[:10],
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
        platform_review=platform_review,
        image_recommendations=(
            _image_recommendations_from_payload(payload, platform_review) if post_format == "image" else []
        ),
        video_recommendations=(
            _video_recommendations_from_payload(payload, platform_review) if post_format == "video" else []
        ),
        video_recommendation=_video_recommendation_from_payload(payload),
        generated_at=datetime.now(timezone.utc),
    )
    idea = _sync_platform_review_from_latest_option(idea)
    return (
        payload.get("evidence_summary", "Grounded in the current report and saved citations.").strip(),
        payload.get("why_now", "This trend is gaining attention right now.").strip(),
        payload.get("caveats"),
        idea,
    )


def _merge_post_options(prior: ContentIdea, new: ContentIdea) -> ContentIdea:
    if new.post_format == "video":
        seen_keys = {_video_option_key(video) for video in prior.video_recommendations}
        merged_videos = list(prior.video_recommendations)
        for video in new.video_recommendations[:1]:
            key = _video_option_key(video)
            if key in seen_keys:
                continue
            merged_videos.append(video)
            seen_keys.add(key)
        merged = new.model_copy(update={"video_recommendations": merged_videos[:MAX_TOTAL_POST_OPTIONS]})
        return _sync_platform_review_from_latest_option(merged)

    seen_keys = {_post_option_key(image) for image in prior.image_recommendations}
    merged_images = list(prior.image_recommendations)
    for image in new.image_recommendations[:1]:
        key = _post_option_key(image)
        if key in seen_keys:
            continue
        merged_images.append(image)
        seen_keys.add(key)

    merged = new.model_copy(update={"image_recommendations": merged_images[:MAX_TOTAL_POST_OPTIONS]})
    return _sync_platform_review_from_latest_option(merged)


def _regenerate_context(prior: ContentIdea | None) -> str:
    if prior is None:
        return ""
    if prior.post_format == "video":
        lines = [
            "",
            "REGENERATION REQUEST:",
            "Add exactly one more short-video option with a new hook, caption, hashtags, and video prompt.",
            "Return exactly one video_recommendations object. It will be appended to prior options.",
            "Make the copy and visual prompt clearly different from every prior option.",
            "Do not reuse prior wording or video prompts verbatim.",
        ]
        for index, video in enumerate(prior.video_recommendations, start=1):
            lines.append(f"Prior option {index} hook: {video.hook or 'none'}")
            lines.append(f"Prior option {index} caption: {video.caption or 'none'}")
            if video.hashtags:
                lines.append(f"Prior option {index} hashtags: {', '.join(video.hashtags)}")
            lines.append(f"Prior option {index} video prompt ({video.label}): {video.prompt}")
        return "\n".join(lines)

    lines = [
        "",
        "REGENERATION REQUEST:",
        "Add exactly one more post option with a new hook, caption, hashtags, and image prompt.",
        "Return exactly one image_recommendation object. It will be appended to prior options.",
        "Make the copy and visual prompt clearly different from every prior option.",
        "Do not reuse prior wording or image prompts verbatim.",
    ]
    for index, image in enumerate(prior.image_recommendations, start=1):
        lines.append(f"Prior option {index} hook: {image.hook or 'none'}")
        lines.append(f"Prior option {index} caption: {image.caption or 'none'}")
        if image.hashtags:
            lines.append(f"Prior option {index} hashtags: {', '.join(image.hashtags)}")
        lines.append(f"Prior option {index} image prompt ({image.label}): {image.prompt}")
    return "\n".join(lines)


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
    platform: SocialPlatform = "instagram",
    post_format: PostFormat = "image",
    settings: Settings | None = None,
) -> tuple[BriefItem, LLMResponse]:
    response = await llm.complete(
        system=platform_brief_system_prompt(platform, post_format),
        user=_brief_item_prompt(
            trend=trend,
            report_summary=report_summary,
            citations=citations,
            region=region,
            research_time=research_time,
            score=score,
            locales=locales,
            platform=platform,
            post_format=post_format,
        ),
    )
    payload = _extract_json_payload(response.content)
    evidence_summary, why_now, caveats, idea = _idea_from_payload(
        payload,
        platform=platform,
        post_format=post_format,
    )
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
    platform: SocialPlatform = "instagram",
    post_format: PostFormat = "image",
    settings: Settings | None = None,
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
        platform=platform,
        post_format=post_format,
        settings=settings,
    )
    platform_label = "Instagram" if platform == "instagram" else "TikTok"
    format_label = "video" if post_format == "video" else "post"
    return TrendBrief(
        id=str(uuid.uuid4()),
        report_id=row.id,
        title=f"{platform_label} {format_label} — {trend.name}",
        summary=f"{platform_label} {format_label} ideas for {trend.name}, grounded in the saved {row.research_time or 'current'} research.",
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
    platform: SocialPlatform = "instagram",
    post_format: PostFormat = "image",
    settings: Settings | None = None,
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
            platform=platform,
            post_format=post_format,
            settings=settings,
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
    platform: SocialPlatform = "instagram",
    post_format: PostFormat | None = None,
    settings: Settings | None = None,
    prior_idea: ContentIdea | None = None,
) -> tuple[ContentIdea, LLMResponse]:
    resolved_format = post_format or (prior_idea.post_format if prior_idea else "image")
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
        system=platform_brief_system_prompt(platform, resolved_format),
        user=_brief_item_prompt(
            trend=trend,
            report_summary=report_summary,
            citations=citations,
            region=region,
            research_time=research_time,
            score=item.score,
            locales=_locale_candidates(region),
            platform=platform,
            post_format=resolved_format,
            regenerate_context=_regenerate_context(prior_idea),
        ),
    )
    payload = _extract_json_payload(response.content)
    _, _, _, idea = _idea_from_payload(payload, platform=platform, post_format=resolved_format)
    if prior_idea is not None:
        idea = idea.model_copy(update={"post_format": prior_idea.post_format})
        idea = _merge_post_options(prior_idea, idea)
    return idea, response
