import httpx

from willbe_trends.config import Settings
from willbe_trends.search.base import RawSearchHit, SearchProvider


class TavilyProvider(SearchProvider):
    name = "tavily"

    def __init__(self, settings: Settings) -> None:
        if not settings.tavily_api_key:
            raise ValueError(
                "TAVILY_API_KEY is required when using the tavily search provider."
            )
        self._api_key = settings.tavily_api_key

    async def search(self, query: str, *, max_results: int = 5) -> list[RawSearchHit]:
        payload = {
            "api_key": self._api_key,
            "query": query,
            "max_results": max_results,
            "search_depth": "basic",
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post("https://api.tavily.com/search", json=payload)
            response.raise_for_status()
            data = response.json()

        hits: list[RawSearchHit] = []
        for row in data.get("results", []):
            hits.append(
                RawSearchHit(
                    title=row.get("title", "").strip(),
                    url=row.get("url", "").strip(),
                    snippet=row.get("content", row.get("snippet", "")).strip(),
                )
            )
        return hits
