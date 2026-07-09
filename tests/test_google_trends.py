from datetime import UTC, datetime

import httpx
import pytest

from willbe_trends.search.google_trends_client import (
    GoogleTrendsClient,
    GoogleTrendsPoint,
    GoogleTrendsSeries,
    query_to_trend_term,
    region_to_geo_code,
    summarize_trend_series,
)
from willbe_trends.search.google_trends_provider import GoogleTrendsProvider


def test_query_to_trend_term_strips_site_and_dates():
    query = "site:allure.com nails trends July 2026"
    assert query_to_trend_term(query) == "nails trends"


def test_region_to_geo_code_defaults_global_to_us():
    assert region_to_geo_code("global") == "US"
    assert region_to_geo_code("Finland") == "FI"


def test_summarize_trend_series_uses_scaled_values():
    series = GoogleTrendsSeries(
        term="nail art",
        geo_code="US",
        points=[
            GoogleTrendsPoint(
                timestamp=datetime(2026, 5, 1, tzinfo=UTC),
                search_interest=12.5,
                scaled_search_interest=55,
            ),
            GoogleTrendsPoint(
                timestamp=datetime(2026, 6, 1, tzinfo=UTC),
                search_interest=18.0,
                scaled_search_interest=78,
            ),
        ],
    )
    summary = summarize_trend_series(series)
    assert "Google Trends scaled interest" in summary
    assert "peak 78" in summary
    assert "latest 78" in summary


@pytest.mark.asyncio
async def test_google_trends_provider_calls_real_api_shape(monkeypatch, tmp_path):
    credentials = tmp_path / "client.json"
    credentials.write_text('{"installed":{"client_id":"x","client_secret":"y"}}', encoding="utf-8")

    async def fake_fetch_time_series(self, term, *, geo_code="US", months=12, time_resolution="MONTH"):
        del self, months, time_resolution
        return GoogleTrendsSeries(
            term=term,
            geo_code=geo_code,
            points=[
                GoogleTrendsPoint(
                    timestamp=datetime(2026, 6, 1, tzinfo=UTC),
                    search_interest=10.0,
                    scaled_search_interest=42,
                )
            ],
        )

    monkeypatch.setattr(GoogleTrendsClient, "fetch_time_series", fake_fetch_time_series)

    from willbe_trends.config import Settings

    provider = GoogleTrendsProvider(
        Settings(
            GOOGLE_TRENDS_PROJECT_ID="demo-project",
            GOOGLE_TRENDS_CREDENTIALS_PATH=credentials,
            GOOGLE_TRENDS_GEO_REGION="global",
        )
    )
    hits = await provider.search("nails trends July 2026", max_results=3)
    assert len(hits) == 1
    assert hits[0].title == "Google Trends: nails trends"
    assert "trends.google.com" in hits[0].url
    assert "scaled interest" in hits[0].snippet


@pytest.mark.asyncio
async def test_google_trends_client_polls_operation(monkeypatch, tmp_path):
    credentials = tmp_path / "service-account.json"
    credentials.write_text(
        '{"type":"service_account","client_email":"demo@demo.iam.gserviceaccount.com","token_uri":"https://oauth2.googleapis.com/token","private_key":"x"}',
        encoding="utf-8",
    )
    client = GoogleTrendsClient(
        project_id="demo-project",
        credentials_path=credentials,
        token_path=tmp_path / "token.json",
    )

    def fake_load_access_token() -> str:
        return "test-token"

    monkeypatch.setattr(client, "_load_access_token", fake_load_access_token)

    poll_calls = {"count": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "POST" and request.url.path.endswith("/fetchTimeSeries"):
            return httpx.Response(200, json={"name": "operations/demo-op"})
        if request.method == "GET" and "/operations/" in request.url.path:
            poll_calls["count"] += 1
            if poll_calls["count"] == 1:
                return httpx.Response(200, json={"done": False})
            return httpx.Response(
                200,
                json={
                    "done": True,
                    "response": {
                        "timeSeries": {
                            "points": [
                                {
                                    "date": "2026-06-01T00:00:00Z",
                                    "searchInterest": 12.5,
                                    "scaledSearchInterest": 60,
                                }
                            ]
                        }
                    },
                },
            )
        return httpx.Response(404)

    original_async_client = httpx.AsyncClient
    monkeypatch.setattr(
        httpx,
        "AsyncClient",
        lambda **kwargs: original_async_client(transport=httpx.MockTransport(handler)),
    )

    series = await client.fetch_time_series("nail art", geo_code="US")
    assert series.term == "nail art"
    assert len(series.points) == 1
    assert series.points[0].scaled_search_interest == 60
