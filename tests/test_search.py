import pytest

from willbe_trends.models.search import PreferredSource, PreferredSourcesConfig
from willbe_trends.models.trends import TrendCategory
from willbe_trends.search.base import RawSearchHit
from willbe_trends.search.gather import build_neutral_queries, build_personalized_queries
from willbe_trends.search.sources import (
    active_sources_for_category,
    match_preferred_source,
    rank_hits,
)
from willbe_trends.search.sources_config import load_sources, reset_sources, save_sources
from willbe_trends.models.preferences import FinishPreference, NailShape, UserPreferences


def test_build_neutral_queries_includes_site_queries():
    queries = build_neutral_queries(
        category=TrendCategory.NAILS,
        region="global",
        preferred_domains=["allure.com", "vogue.com"],
        research_time="July 2026",
    )
    assert any("site:allure.com" in query for query in queries)
    assert any("nails trends July 2026" in query for query in queries)


def test_preferred_source_matching_and_ranking():
    sources = [
        PreferredSource(name="Allure", domain="allure.com", weight=2.0),
        PreferredSource(name="Other", domain="example.com", weight=0.5),
    ]
    hits = [
        RawSearchHit(title="Generic", url="https://random.com/a", snippet="a"),
        RawSearchHit(title="Allure", url="https://www.allure.com/story", snippet="b"),
    ]
    ranked = rank_hits(hits, sources)
    assert ranked[0][0].title == "Allure"
    assert match_preferred_source("https://beauty.allure.com/x", sources).name == "Allure"


def test_active_sources_filters_by_category():
    config = PreferredSourcesConfig(
        sources=[
            PreferredSource(
                name="Nails",
                domain="nails.com",
                categories=[TrendCategory.NAILS],
            ),
            PreferredSource(name="Unscoped", domain="open.com", categories=[]),
        ]
    )
    active = active_sources_for_category(config, TrendCategory.NAILS)
    assert {source.domain for source in active} == {"nails.com", "open.com"}


def test_load_preferred_sources_from_yaml(tmp_path):
    path = tmp_path / "sources.yaml"
    path.write_text(
        "version: 1\nsources:\n  - name: Vogue\n    domain: vogue.com\n    enabled: true\n"
    )
    config = load_sources(path)
    assert config.sources[0].domain == "vogue.com"


def test_save_and_reset_sources(tmp_path, monkeypatch):
    path = tmp_path / "sources.yaml"
    monkeypatch.setenv("WILLBE_PREFERRED_SOURCES_PATH", str(path))

    from willbe_trends.config import get_settings

    get_settings.cache_clear()

    config = PreferredSourcesConfig(
        sources=[PreferredSource(name="Allure", domain="allure.com", weight=2.0)]
    )
    save_sources(config, path)
    loaded = load_sources(path)
    assert loaded.sources[0].domain == "allure.com"

    reset = reset_sources(path)
    assert reset.sources[0].domain == "allure.com"
    assert len(reset.sources) == 8
    assert path.exists()

    get_settings.cache_clear()


def test_build_personalized_queries_use_preferences():
    prefs = UserPreferences(
        favorite_colors=["cherry red"],
        preferred_shapes=[NailShape.ALMOND],
        preferred_finishes=[FinishPreference.CHROME],
        style_keywords=["minimalist"],
    )
    queries = build_personalized_queries(
        category=TrendCategory.NAILS,
        region="global",
        preferences=prefs,
        preferred_domains=["allure.com"],
        research_time="Summer 2026",
    )
    assert any("cherry red" in query for query in queries)
    assert any("minimalist" in query for query in queries)
