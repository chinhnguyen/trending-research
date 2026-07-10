from pathlib import Path

from willbe_trends.config import Settings, get_settings
from willbe_trends.media.base import ImageGenerationResult
from willbe_trends.media.openai_images import OpenAIImageGenerator

PROBE_FILE = Path("data/.openai_image_probe_ok")
_TEST_PROMPT = "Close-up salon manicure with soft chrome finish, neutral background, product photo style."


def probe_file_path(settings: Settings | None = None) -> Path:
    resolved = settings or get_settings()
    if resolved.willbe_database_url.startswith("sqlite:///./"):
        return PROBE_FILE
    # Keep probe beside sqlite file for non-default DB paths.
    db_path = resolved.willbe_database_url.removeprefix("sqlite:///")
    return Path(db_path).parent / ".openai_image_probe_ok"


def is_image_generation_allowed(settings: Settings | None = None) -> bool:
    resolved = settings or get_settings()
    if not resolved.openai_api_key:
        return False
    probed = probe_file_path(resolved).is_file()
    if resolved.willbe_media_require_probe and not probed:
        return False
    # A successful probe is enough for local/dev; set WILLBE_MEDIA_GENERATION_ENABLED for prod.
    return resolved.willbe_media_generation_enabled or probed


def mark_image_probe_passed(settings: Settings | None = None) -> Path:
    path = probe_file_path(settings)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("ok\n", encoding="utf-8")
    return path


async def run_image_generation_test(
    *,
    settings: Settings | None = None,
    prompt: str = _TEST_PROMPT,
    aspect_ratio: str = "1:1",
) -> ImageGenerationResult:
    resolved = settings or get_settings()
    generator = OpenAIImageGenerator(resolved)
    return await generator.generate(prompt=prompt, aspect_ratio=aspect_ratio)
