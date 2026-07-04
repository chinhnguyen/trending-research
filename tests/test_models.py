import json

import pytest

from willbe_trends.models.preferences import FinishPreference, NailShape, UserPreferences
from willbe_trends.research.neutral import build_trend_report
from willbe_trends.models.trends import TrendCategory


SAMPLE_LLM_JSON = json.dumps(
    {
        "summary": "Soft neutrals and chrome accents dominate.",
        "trends": [
            {
                "name": "Milky French",
                "description": "Sheer milky bases with crisp French tips.",
                "popularity": "rising",
                "colors": ["milky white", "nude pink"],
                "techniques": ["soft gel", "micro French"],
                "tags": ["clean girl", "minimal"],
                "confidence": 0.82,
                "source_hint": "Instagram salons",
            }
        ],
    }
)


def test_build_trend_report_parses_json():
    report = build_trend_report(
        category=TrendCategory.NAILS,
        mode="neutral",
        llm_response_text=SAMPLE_LLM_JSON,
        provider="openai",
        model="gpt-4o-mini",
    )
    assert report.mode == "neutral"
    assert len(report.trends) == 1
    assert report.trends[0].name == "Milky French"


def test_user_preferences_sample_file():
    prefs = UserPreferences(
        display_name="Test",
        favorite_colors=["red"],
        preferred_shapes=[NailShape.ALMOND],
        preferred_finishes=[FinishPreference.GLOSSY],
        style_keywords=["minimalist"],
    )
    assert prefs.display_name == "Test"
