from willbe_trends.models.category import TrendCategory
from willbe_trends.models.search import PreferredSource, PreferredSourcesConfig

DEFAULT_PREFERRED_SOURCES: list[PreferredSource] = [
    PreferredSource(
        name="Allure",
        domain="allure.com",
        weight=1.0,
        categories=[TrendCategory.NAILS],
        enabled=True,
    ),
    PreferredSource(
        name="Vogue",
        domain="vogue.com",
        weight=0.95,
        categories=[TrendCategory.NAILS],
        enabled=True,
    ),
    PreferredSource(
        name="Marie Claire",
        domain="marieclaire.com",
        weight=0.9,
        categories=[TrendCategory.NAILS],
        enabled=True,
    ),
    PreferredSource(
        name="Byrdie",
        domain="byrdie.com",
        weight=0.9,
        categories=[TrendCategory.NAILS],
        enabled=True,
    ),
    PreferredSource(
        name="Who What Wear",
        domain="whowhatwear.com",
        weight=0.85,
        categories=[TrendCategory.NAILS],
        enabled=True,
    ),
    PreferredSource(
        name="Refinery29",
        domain="refinery29.com",
        weight=0.8,
        categories=[TrendCategory.NAILS],
        enabled=True,
    ),
    PreferredSource(
        name="Pinterest",
        domain="pinterest.com",
        weight=0.7,
        categories=[TrendCategory.NAILS],
        enabled=True,
    ),
    PreferredSource(
        name="Google Trends",
        domain="trends.google.com",
        weight=0.95,
        categories=[TrendCategory.NAILS],
        enabled=True,
    ),
]


def default_preferred_sources_config() -> PreferredSourcesConfig:
    return PreferredSourcesConfig(sources=list(DEFAULT_PREFERRED_SOURCES))
