from pathlib import Path

import yaml
from pydantic import ValidationError

from willbe_trends.config import Settings, get_settings
from willbe_trends.models.prompts import PromptConfig


def default_prompts() -> PromptConfig:
    return PromptConfig()


def load_prompts(path: Path | None = None) -> PromptConfig:
    settings = get_settings()
    target = path or settings.willbe_prompts_path
    if not target.exists():
        return default_prompts()

    raw = yaml.safe_load(target.read_text(encoding="utf-8")) or {}
    try:
        return PromptConfig.model_validate(raw)
    except ValidationError as exc:
        raise ValueError(f"Invalid prompts config at {target}: {exc}") from exc


def save_prompts(config: PromptConfig, path: Path | None = None) -> Path:
    settings = get_settings()
    target = path or settings.willbe_prompts_path
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = config.model_dump()
    target.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")
    return target


def reset_prompts(path: Path | None = None) -> PromptConfig:
    config = default_prompts()
    save_prompts(config, path)
    return config
