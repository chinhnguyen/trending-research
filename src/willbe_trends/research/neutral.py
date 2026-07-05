import json
import re
from datetime import datetime, timezone
from pathlib import Path

from willbe_trends.config import Settings, get_settings
from willbe_trends.llm.base import LLMProvider
from willbe_trends.models.prompts import PromptConfig
from willbe_trends.models.search import WebResearchBundle
from willbe_trends.models.trends import TrendCategory, TrendReport, TrendSignal
from willbe_trends.models.usage import LLMUsageStats
from willbe_trends.research.prompts_config import load_prompts
from willbe_trends.research.time_context import normalize_research_time
from willbe_trends.search.gather import (
    build_neutral_queries,
    format_web_context,
    gather_web_research,
)
from willbe_trends.search.images import enrich_trends_with_images
from willbe_trends.search.sources import active_sources_for_category, load_preferred_sources


def _extract_json_payload(text: str) -> dict:
    """Parse JSON from a model response, tolerating markdown fences."""
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


def build_trend_report(
    *,
    category: TrendCategory,
    mode: str,
    research_time: str,
    llm_response_text: str,
    provider: str,
    model: str,
    web_research: WebResearchBundle | None = None,
    llm_usage: LLMUsageStats | None = None,
) -> TrendReport:
    payload = _extract_json_payload(llm_response_text)

    trends = [TrendSignal.model_validate(item) for item in payload.get("trends", [])]
    summary = payload.get("summary", "").strip()
    if not summary:
        raise ValueError("Model response missing required 'summary' field.")

    return TrendReport(
        category=category,
        mode=mode,
        research_time=research_time,
        summary=summary,
        trends=trends,
        generated_at=datetime.now(timezone.utc).isoformat(),
        llm_provider=provider,
        llm_model=model,
        llm_usage=llm_usage,
        web_research=web_research,
    )


def build_neutral_user_prompt(
    *,
    category: TrendCategory,
    region: str,
    research_time: str,
    web_bundle: WebResearchBundle | None,
    prompts: PromptConfig | None = None,
) -> str:
    config = prompts or load_prompts()
    parts = [
        config.neutral_user_template.format(
            category=category.value,
            region=region,
            research_time=research_time,
        )
    ]
    if web_bundle:
        parts.extend(["", format_web_context(web_bundle)])
    return "\n".join(parts)


async def _maybe_gather_web_context(
    *,
    category: TrendCategory,
    region: str,
    research_time: str,
    web_search: bool,
    preferred_sources_path: Path | None,
    settings: Settings | None = None,
) -> WebResearchBundle | None:
    resolved = settings or get_settings()
    if not web_search or not resolved.willbe_web_search_enabled:
        return None

    sources_path = preferred_sources_path or resolved.willbe_preferred_sources_path
    preferred_config = load_preferred_sources(sources_path)
    preferred_sources = active_sources_for_category(preferred_config, category)
    preferred_domains = [source.domain for source in preferred_sources]

    queries = build_neutral_queries(
        category=category,
        region=region,
        preferred_domains=preferred_domains,
        research_time=research_time,
    )
    return await gather_web_research(
        queries=queries,
        preferred_sources_path=sources_path,
        category=category,
        max_results_per_query=resolved.willbe_search_max_results_per_query,
        max_total_citations=resolved.willbe_search_max_citations,
        settings=resolved,
    )


async def research_neutral_trends(
    *,
    category: TrendCategory,
    llm: LLMProvider,
    region: str = "global",
    research_time: str | None = None,
    web_search: bool = True,
    preferred_sources_path: Path | None = None,
    settings: Settings | None = None,
    prompts: PromptConfig | None = None,
) -> TrendReport:
    resolved_time = normalize_research_time(research_time)
    prompt_config = prompts or load_prompts()
    web_bundle = await _maybe_gather_web_context(
        category=category,
        region=region,
        research_time=resolved_time,
        web_search=web_search,
        preferred_sources_path=preferred_sources_path,
        settings=settings,
    )

    user_prompt = build_neutral_user_prompt(
        category=category,
        region=region,
        research_time=resolved_time,
        web_bundle=web_bundle,
        prompts=prompt_config,
    )
    response = await llm.complete(system=prompt_config.neutral_system(), user=user_prompt)
    report = build_trend_report(
        category=category,
        mode="neutral",
        research_time=resolved_time,
        llm_response_text=response.content,
        provider=response.provider,
        model=response.model,
        web_research=web_bundle,
        llm_usage=response.usage,
    )
    return await enrich_trends_with_images(
        report,
        category=category,
        settings=settings or get_settings(),
    )