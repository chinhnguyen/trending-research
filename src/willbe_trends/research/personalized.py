from pathlib import Path

from willbe_trends.config import Settings, get_settings
from willbe_trends.llm.base import LLMProvider
from willbe_trends.models.preferences import UserPreferences
from willbe_trends.models.prompts import PromptConfig
from willbe_trends.models.search import WebResearchBundle
from willbe_trends.models.trends import TrendCategory, TrendReport
from willbe_trends.research.neutral import build_trend_report
from willbe_trends.research.prompts_config import load_prompts
from willbe_trends.research.time_context import normalize_research_time
from willbe_trends.search.gather import (
    build_personalized_queries,
    format_web_context,
    gather_web_research,
)
from willbe_trends.search.images import enrich_trends_with_images
from willbe_trends.search.sources import active_sources_for_category, load_preferred_sources


def build_personalized_user_prompt(
    *,
    category: TrendCategory,
    region: str,
    research_time: str,
    preferences: UserPreferences,
    web_bundle: WebResearchBundle | None,
    prompts: PromptConfig | None = None,
) -> str:
    config = prompts or load_prompts()
    parts = [
        config.personalized_user_template.format(
            category=category.value,
            region=region,
            research_time=research_time,
            preferences_json=preferences.model_dump_json(indent=2),
        )
    ]
    if web_bundle:
        parts.extend(["", format_web_context(web_bundle)])
    return "\n".join(parts)


async def research_personalized_trends(
    *,
    category: TrendCategory,
    preferences: UserPreferences,
    llm: LLMProvider,
    region: str = "global",
    research_time: str | None = None,
    web_search: bool = True,
    preferred_sources_path: Path | None = None,
    settings: Settings | None = None,
    prompts: PromptConfig | None = None,
) -> TrendReport:
    resolved = settings or get_settings()
    resolved_time = normalize_research_time(research_time)
    prompt_config = prompts or load_prompts()
    web_bundle: WebResearchBundle | None = None

    if web_search and resolved.willbe_web_search_enabled:
        sources_path = preferred_sources_path or resolved.willbe_preferred_sources_path
        preferred_config = load_preferred_sources(sources_path)
        preferred_sources = active_sources_for_category(preferred_config, category)
        preferred_domains = [source.domain for source in preferred_sources]
        queries = build_personalized_queries(
            category=category,
            region=region,
            preferences=preferences,
            preferred_domains=preferred_domains,
            research_time=resolved_time,
        )
        web_bundle = await gather_web_research(
            queries=queries,
            preferred_sources_path=sources_path,
            category=category,
            max_results_per_query=resolved.willbe_search_max_results_per_query,
            max_total_citations=resolved.willbe_search_max_citations,
            settings=resolved,
        )

    user_prompt = build_personalized_user_prompt(
        category=category,
        region=region,
        research_time=resolved_time,
        preferences=preferences,
        web_bundle=web_bundle,
        prompts=prompt_config,
    )
    response = await llm.complete(
        system=prompt_config.personalized_system(),
        user=user_prompt,
    )
    report = build_trend_report(
        category=category,
        mode="personalized",
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
        preferences=preferences,
        settings=resolved,
    )
