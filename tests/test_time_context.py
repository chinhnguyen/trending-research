from willbe_trends.research.time_context import default_research_time, normalize_research_time


def test_normalize_research_time_uses_default_when_empty():
    assert normalize_research_time(None) == default_research_time()
    assert normalize_research_time("  ") == default_research_time()


def test_normalize_research_time_preserves_custom_value():
    assert normalize_research_time("Summer 2026") == "Summer 2026"
