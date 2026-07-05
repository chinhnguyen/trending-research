from urllib.parse import urlparse

from willbe_trends.models.search import PreferredSource, PreferredSourcesConfig
from willbe_trends.models.trends import TrendCategory
from willbe_trends.search.sources_config import load_sources


def load_preferred_sources(path) -> PreferredSourcesConfig:
    return load_sources(path)


def active_sources_for_category(
    config: PreferredSourcesConfig,
    category: TrendCategory,
) -> list[PreferredSource]:
    active: list[PreferredSource] = []
    for source in config.sources:
        if not source.enabled:
            continue
        if source.categories and category not in source.categories:
            continue
        active.append(source)
    return sorted(active, key=lambda item: item.weight, reverse=True)


def domain_from_url(url: str) -> str:
    host = urlparse(url).netloc.lower()
    if host.startswith("www."):
        host = host[4:]
    return host


def match_preferred_source(
    url: str, sources: list[PreferredSource]
) -> PreferredSource | None:
    domain = domain_from_url(url)
    if not domain:
        return None
    for source in sources:
        preferred_domain = source.domain.lower().removeprefix("www.")
        if domain == preferred_domain or domain.endswith(f".{preferred_domain}"):
            return source
    return None


def rank_hits(
    hits,
    preferred_sources: list[PreferredSource],
):
    ranked = []
    for hit in hits:
        matched = match_preferred_source(hit.url, preferred_sources)
        score = matched.weight if matched else 0.0
        ranked.append((hit, matched, score))
    return sorted(ranked, key=lambda item: item[2], reverse=True)
