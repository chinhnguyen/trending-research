from willbe_trends.config import SearchProviderName, Settings, get_settings
from willbe_trends.search.base import SearchProvider
from willbe_trends.search.duckduckgo_provider import DuckDuckGoProvider
from willbe_trends.search.tavily_provider import TavilyProvider

PROVIDER_FACTORIES: dict[str, type[SearchProvider]] = {
    DuckDuckGoProvider.name: DuckDuckGoProvider,
    TavilyProvider.name: TavilyProvider,
}


def list_search_providers() -> list[str]:
    return sorted(PROVIDER_FACTORIES.keys())


def create_search_provider(
    provider: SearchProviderName | None = None,
    settings: Settings | None = None,
) -> SearchProvider:
    resolved = settings or get_settings()
    provider_name = provider or resolved.willbe_search_provider
    factory = PROVIDER_FACTORIES.get(provider_name)
    if factory is None:
        supported = ", ".join(list_search_providers())
        raise ValueError(
            f"Unknown search provider '{provider_name}'. Supported: {supported}"
        )
    return factory(resolved)
