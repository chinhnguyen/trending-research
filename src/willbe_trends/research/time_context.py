from datetime import datetime, timezone


def default_research_time() -> str:
    """Human-readable default, e.g. 'July 2026'."""
    return datetime.now(timezone.utc).strftime("%B %Y")


def normalize_research_time(value: str | None) -> str:
    if value and value.strip():
        return value.strip()
    return default_research_time()
