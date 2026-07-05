import pytest

from willbe_trends.models.trends import TrendCategory, TrendReport, TrendSignal
from willbe_trends.search.base import RawImageHit
from willbe_trends.search.duckduckgo_provider import DuckDuckGoProvider
from willbe_trends.search.images import build_trend_image_query, enrich_trends_with_images


class FakeImageProvider(DuckDuckGoProvider):
    async def search_images(self, query: str, *, max_results: int = 3):
        del max_results
        return [
            RawImageHit(
                image_url=f"https://images.example/{query.replace(' ', '-')}.jpg",
                source_url="https://example.com/nails",
                title=query,
            )
        ]


@pytest.mark.asyncio
async def test_enrich_trends_with_images():
    report = TrendReport(
        category=TrendCategory.NAILS,
        mode="neutral",
        research_time="July 2026",
        summary="Visual trends",
        trends=[
            TrendSignal(
                name="Glazed Jelly Nails",
                description="Sheer glossy finish",
                popularity="rising",
                colors=["pink"],
            )
        ],
        generated_at="2026-07-04T12:00:00+00:00",
        llm_provider="openai",
        llm_model="gpt-4o-mini",
    )

    enriched = await enrich_trends_with_images(
        report,
        category=TrendCategory.NAILS,
        search=FakeImageProvider(),
    )

    assert enriched.trends[0].image_url is not None
    assert enriched.trends[0].image_source_url == "https://example.com/nails"
    assert "Glazed-Jelly-Nails" in enriched.trends[0].image_url


def test_build_trend_image_query():
    trend = TrendSignal(
        name="Cherry French",
        description="Red tips",
        popularity="steady",
        colors=["cherry red"],
    )
    query = build_trend_image_query(
        trend,
        category=TrendCategory.NAILS,
        research_time="July 2026",
    )
    assert "Cherry French" in query
    assert "nail art" in query
