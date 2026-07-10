"""OpenAI Sora short-form video generation."""

import asyncio

from openai import AsyncOpenAI

from willbe_trends.config import Settings
from willbe_trends.media.base import ShortVideoGenerator, VideoGenerationResult
from willbe_trends.media.progress import ProgressCallback, report_progress

_SORA_MODELS = ("sora-2-pro", "sora-2")
_DEFAULT_MODEL = "sora-2"
_SORA_SIZES = {
    "9:16": "720x1280",
    "16:9": "1280x720",
    "1:1": "720x1280",
}
_VALID_SECONDS = (4, 8, 12, 16, 20)
_POLL_INTERVAL_SECONDS = 5
_POLL_TIMEOUT_SECONDS = 300


def _size_for_aspect(aspect_ratio: str) -> str:
    return _SORA_SIZES.get(aspect_ratio, "720x1280")


def _seconds_for_duration(duration_seconds: int) -> str:
    closest = min(_VALID_SECONDS, key=lambda value: abs(value - duration_seconds))
    return str(closest)


def _models_to_try(configured: str) -> list[str]:
    ordered: list[str] = []
    for candidate in (configured, *_SORA_MODELS):
        if candidate and candidate not in ordered:
            ordered.append(candidate)
    return ordered or [_DEFAULT_MODEL]


def _friendly_error(exc: Exception | None, tried_models: list[str]) -> str | None:
    if exc is None:
        return None
    models = ", ".join(tried_models)
    message = str(exc).lower()
    if "does not exist" in message or ("invalid" in message and "model" in message):
        return (
            f"OpenAI video generation failed for models: {models}. "
            "Check OPENAI_VIDEO_MODEL and your API access to Sora."
        )
    return (
        "Video could not be generated. Confirm Sora API access on your OpenAI account, "
        "or use the storyboard prompts with your own salon footage."
    )


class OpenAISoraGenerator(ShortVideoGenerator):
    name = "openai_sora"

    def __init__(self, settings: Settings) -> None:
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required for OpenAI video generation.")
        self._client = AsyncOpenAI(api_key=settings.openai_api_key)
        self._model = settings.openai_video_model

    async def generate(
        self,
        *,
        prompt: str,
        aspect_ratio: str,
        duration_seconds: int,
        on_progress: ProgressCallback | None = None,
    ) -> VideoGenerationResult:
        tried: list[str] = []
        last_exc: Exception | None = None
        size = _size_for_aspect(aspect_ratio)
        seconds = _seconds_for_duration(duration_seconds)

        for model in _models_to_try(self._model):
            tried.append(model)
            try:
                job = await self._client.videos.create(
                    model=model,
                    prompt=prompt,
                    size=size,
                    seconds=seconds,
                )
                await report_progress(on_progress, "Rendering video…", 15)
                completed = await self._wait_for_completion(job.id, on_progress=on_progress)
                if completed.status != "completed":
                    error = getattr(getattr(completed, "error", None), "message", None)
                    return VideoGenerationResult(
                        data=None,
                        provider=self.name,
                        model=model,
                        status="failed",
                        error=error or f"Video job finished with status {completed.status}.",
                    )
                content = await self._client.videos.download_content(completed.id)
                data = content.read()
                if not data:
                    raise RuntimeError("Video API returned empty content.")
                return VideoGenerationResult(
                    data=data,
                    provider=self.name,
                    model=model,
                    status="generated",
                )
            except Exception as exc:  # noqa: BLE001
                last_exc = exc
                message = str(exc).lower()
                if "does not exist" in message or ("invalid" in message and "model" in message):
                    continue
                break

        return VideoGenerationResult(
            data=None,
            provider=self.name,
            model=self._model,
            status="failed",
            error=_friendly_error(last_exc, tried),
        )

    async def _wait_for_completion(self, video_id: str, *, on_progress: ProgressCallback | None = None):
        elapsed = 0
        job = await self._client.videos.retrieve(video_id)
        while job.status in {"queued", "in_progress"} and elapsed < _POLL_TIMEOUT_SECONDS:
            progress = getattr(job, "progress", None)
            if progress is not None:
                stage = "Queued for video render…" if job.status == "queued" else "Rendering video…"
                await report_progress(on_progress, stage, int(progress))
            await asyncio.sleep(_POLL_INTERVAL_SECONDS)
            elapsed += _POLL_INTERVAL_SECONDS
            job = await self._client.videos.retrieve(video_id)
        if job.status == "completed":
            await report_progress(on_progress, "Finalizing video…", 95)
        return job
