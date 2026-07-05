from willbe_trends.config import SearchProviderName, Settings, get_settings
from willbe_trends.search.base import SearchProvider
from willbe_trends.search.duckduckgo_provider import DuckDuckGoProvider
from willbe_trends.search.registry import create_search_provider, list_search_providers
from willbe_trends.search.tavily_provider import TavilyProvider

__all__ = [
    "SearchProvider",
    "create_search_provider",
    "list_search_providers",
]
