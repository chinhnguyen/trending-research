from willbe_trends.config import Settings, get_settings
from willbe_trends.models.preferences import UserPreferences
from willbe_trends.models.trends import TrendCategory, TrendReport, TrendSignal
from willbe_trends.search.base import RawImageHit, SearchProvider
from willbe_trends.search.duckduckgo_provider import DuckDuckGoProvider


def build_trend_image_query(
    trend: TrendSignal,
    *,
    category: TrendCategory,
    research_time: str,
    preferences: UserPreferences | None = None,
) -> str:
    parts = [trend.name, category.value, "nail art", "manicure", research_time]
    if trend.colors:
        parts.extend(trend.colors[:2])
    if preferences:
        parts.extend(preferences.style_keywords[:2])
    return " ".join(part for part in parts if part)


async def enrich_trends_with_images(
    report: TrendReport,
    *,
    category: TrendCategory,
    preferences: UserPreferences | None = None,
    search: SearchProvider | None = None,
    settings: Settings | None = None,
) -> TrendReport:
    resolved = settings or get_settings()
    if not resolved.willbe_image_search_enabled:
        return report

    provider = search or DuckDuckGoProvider(resolved)
    enriched: list[TrendSignal] = []

    for trend in report.trends:
        if trend.image_url:
            enriched.append(trend)
            continue

        query = build_trend_image_query(
            trend,
            category=category,
            research_time=report.research_time,
            preferences=preferences,
        )
        hits = await provider.search_images(
            query,
            max_results=resolved.willbe_image_search_max_results,
        )
        if not hits:
            enriched.append(trend)
            continue

        best = hits[0]
        enriched.append(
            trend.model_copy(
                update={
                    "image_url": best.image_url,
                    "image_source_url": best.source_url,
                    "image_alt": best.title or trend.name,
                }
            )
        )

    return report.model_copy(update={"trends": enriched})
