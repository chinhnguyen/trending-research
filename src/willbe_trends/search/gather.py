from pathlib import Path
from urllib.parse import quote_plus

from willbe_trends.config import Settings, get_settings
from willbe_trends.models.preferences import UserPreferences
from willbe_trends.models.search import WebCitation, WebResearchBundle
from willbe_trends.models.trends import TrendCategory
from willbe_trends.search.base import RawSearchHit, SearchProvider
from willbe_trends.search.registry import create_search_provider
from willbe_trends.search.google_trends_client import (
    GoogleTrendsClient,
    query_to_trend_term,
    region_to_geo_code,
    summarize_trend_series,
)
from willbe_trends.search.sources import (
    active_sources_for_category,
    domain_from_url,
    load_preferred_sources,
    rank_hits,
)


def build_neutral_queries(
    *,
    category: TrendCategory,
    region: str,
    preferred_domains: list[str],
    research_time: str,
) -> list[str]:
    base = [
        f"{category.value} trends {research_time}",
        f"popular {category.value} colors shapes finishes {research_time}",
        f"{category.value} nail art trends {region} {research_time}",
    ]
    site_queries = [
        f"site:{domain} {category.value} trends {research_time}"
        for domain in preferred_domains[:5]
    ]
    return base + site_queries


def build_personalized_queries(
    *,
    category: TrendCategory,
    region: str,
    preferences: UserPreferences,
    preferred_domains: list[str],
    research_time: str,
) -> list[str]:
    style = " ".join(preferences.style_keywords[:3])
    colors = " ".join(preferences.favorite_colors[:3])
    base = [
        f"{category.value} trends {style} {colors} {research_time}",
        f"{category.value} nail art {style} {region} {research_time}",
    ]
    site_queries = [
        f"site:{domain} {category.value} {style} trends {research_time}"
        for domain in preferred_domains[:3]
    ]
    return base + site_queries


def format_web_context(bundle: WebResearchBundle) -> str:
    if not bundle.citations:
        return "No web results were retrieved."

    lines = [
        "Use the following web research snippets as primary evidence.",
        "Prefer claims supported by these sources; note source_hint where relevant.",
        "",
    ]
    for index, citation in enumerate(bundle.citations, start=1):
        preferred = " [preferred source]" if citation.preferred else ""
        lines.extend(
            [
                f"[{index}] {citation.title}{preferred}",
                f"URL: {citation.url}",
                f"Snippet: {citation.snippet}",
                "",
            ]
        )
    return "\n".join(lines).strip()


async def gather_web_research(
    *,
    queries: list[str],
    search: SearchProvider | None = None,
    preferred_sources_path: Path | None = None,
    category: TrendCategory = TrendCategory.NAILS,
    max_results_per_query: int = 4,
    max_total_citations: int = 10,
    settings: Settings | None = None,
    region: str = "global",
) -> WebResearchBundle:
    resolved_settings = settings or get_settings()
    provider = search or create_search_provider(settings=resolved_settings)
    sources_path = preferred_sources_path or resolved_settings.willbe_preferred_sources_path
    preferred_config = load_preferred_sources(sources_path)
    preferred_sources = active_sources_for_category(preferred_config, category)

    seen_urls: set[str] = set()
    collected: list[tuple[RawSearchHit, str]] = []

    for query in queries:
        hits = await provider.search(query, max_results=max_results_per_query)
        for hit in hits:
            if not hit.url or hit.url in seen_urls:
                continue
            seen_urls.add(hit.url)
            collected.append((hit, query))

    if (
        resolved_settings.google_trends_configured()
        and provider.name != "google_trends"
    ):
        trends_hits = await _google_trends_hits(
            queries=queries,
            settings=resolved_settings,
            region=region,
        )
        for hit, query in trends_hits:
            if hit.url in seen_urls:
                continue
            seen_urls.add(hit.url)
            collected.append((hit, query))

    ranked = rank_hits([hit for hit, _ in collected], preferred_sources)
    query_by_url = {hit.url: query for hit, query in collected}
    citations: list[WebCitation] = []
    for hit, matched, _score in ranked:
        citations.append(
            WebCitation(
                title=hit.title,
                url=hit.url,
                snippet=hit.snippet,
                preferred=matched is not None,
                source_name=matched.name if matched else None,
                query=query_by_url.get(hit.url, ""),
            )
        )
        if len(citations) >= max_total_citations:
            break

    return WebResearchBundle(
        enabled=True,
        search_provider=provider.name,
        queries=queries,
        citations=citations,
    )


async def _google_trends_hits(
    *,
    queries: list[str],
    settings: Settings,
    region: str,
) -> list[tuple[RawSearchHit, str]]:
    client = GoogleTrendsClient(
        project_id=settings.google_trends_project_id,
        credentials_path=settings.google_trends_credentials_path,
        token_path=settings.google_trends_token_path,
    )
    geo_code = region_to_geo_code(region or settings.google_trends_geo_region)
    hits: list[tuple[RawSearchHit, str]] = []
    seen_terms: set[str] = set()

    for query in queries[:3]:
        term = query_to_trend_term(query)
        key = term.lower()
        if key in seen_terms:
            continue
        seen_terms.add(key)
        series = await client.fetch_time_series(term, geo_code=geo_code)
        explore_url = (
            "https://trends.google.com/trends/explore?"
            f"q={quote_plus(series.term)}&geo={series.geo_code}"
        )
        hits.append(
            (
                RawSearchHit(
                    title=f"Google Trends: {series.term}",
                    url=explore_url,
                    snippet=summarize_trend_series(series),
                ),
                query,
            )
        )
    return hits


def query_domain(query: str) -> str | None:
    if "site:" not in query:
        return None
    return query.split("site:", 1)[1].split()[0].lower().removeprefix("www.")
