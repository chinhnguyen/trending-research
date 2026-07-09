from urllib.parse import quote_plus

from willbe_trends.config import Settings
from willbe_trends.search.base import RawSearchHit, SearchProvider
from willbe_trends.search.google_trends_client import (
    GoogleTrendsClient,
    query_to_trend_term,
    region_to_geo_code,
    summarize_trend_series,
)


class GoogleTrendsProvider(SearchProvider):
    name = "google_trends"

    def __init__(self, settings: Settings) -> None:
        if not settings.google_trends_configured():
            raise ValueError(
                "GOOGLE_TRENDS_PROJECT_ID and GOOGLE_TRENDS_CREDENTIALS_PATH are required "
                "when using the google_trends search provider."
            )
        self._client = GoogleTrendsClient(
            project_id=settings.google_trends_project_id,
            credentials_path=settings.google_trends_credentials_path,
            token_path=settings.google_trends_token_path,
        )
        self._default_geo_code = region_to_geo_code(settings.google_trends_geo_region)

    async def search(self, query: str, *, max_results: int = 5) -> list[RawSearchHit]:
        del max_results
        term = query_to_trend_term(query)
        series = await self._client.fetch_time_series(term, geo_code=self._default_geo_code)
        snippet = summarize_trend_series(series)
        explore_url = (
            "https://trends.google.com/trends/explore?"
            f"q={quote_plus(series.term)}&geo={series.geo_code}"
        )
        return [
            RawSearchHit(
                title=f"Google Trends: {series.term}",
                url=explore_url,
                snippet=snippet,
            )
        ]
