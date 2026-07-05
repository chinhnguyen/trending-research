from pathlib import Path

import yaml
from pydantic import ValidationError

from willbe_trends.config import get_settings
from willbe_trends.models.search import PreferredSourcesConfig
from willbe_trends.search.source_defaults import default_preferred_sources_config


def default_sources() -> PreferredSourcesConfig:
    return default_preferred_sources_config()


def load_sources(path: Path | None = None) -> PreferredSourcesConfig:
    settings = get_settings()
    target = path or settings.willbe_preferred_sources_path
    if not target.exists():
        return default_sources()

    raw = yaml.safe_load(target.read_text(encoding="utf-8")) or {}
    try:
        return PreferredSourcesConfig.model_validate(raw)
    except ValidationError as exc:
        raise ValueError(f"Invalid preferred sources config at {target}: {exc}") from exc


def save_sources(config: PreferredSourcesConfig, path: Path | None = None) -> Path:
    settings = get_settings()
    target = path or settings.willbe_preferred_sources_path
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = config.model_dump(mode="json")
    target.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")
    return target


def reset_sources(path: Path | None = None) -> PreferredSourcesConfig:
    config = default_sources()
    save_sources(config, path)
    return config
