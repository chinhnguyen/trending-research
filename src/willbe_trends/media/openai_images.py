"""OpenAI GPT Image generation (DALL-E removed from API May 2026)."""

from openai import AsyncOpenAI

from willbe_trends.config import Settings
from willbe_trends.media.base import ImageGenerationResult, ImageGenerator

_GPT_IMAGE_MODELS = (
    "gpt-image-2",
    "gpt-image-1.5",
    "gpt-image-1",
    "gpt-image-1-mini",
)
_DEFAULT_MODEL = "gpt-image-1-mini"

_GPT_SIZES = {
    "1:1": "1024x1024",
    "4:5": "1024x1536",
    "9:16": "1024x1536",
    "16:9": "1536x1024",
}


def _size_for_aspect(aspect_ratio: str) -> str:
    return _GPT_SIZES.get(aspect_ratio, "1024x1024")


def _is_gpt_image_model(model: str) -> bool:
    return model.startswith("gpt-image") or model == "chatgpt-image-latest"


def _is_invalid_model_error(exc: Exception) -> bool:
    message = str(exc).lower()
    return "does not exist" in message or ("invalid" in message and "model" in message)


def _models_to_try(configured: str) -> list[str]:
    ordered: list[str] = []
    for candidate in (configured, *_GPT_IMAGE_MODELS):
        if candidate and candidate not in ordered and _is_gpt_image_model(candidate):
            ordered.append(candidate)
    return ordered or [_DEFAULT_MODEL]


def _image_url_from_response(response) -> str | None:
    if not response.data:
        return None
    item = response.data[0]
    if item.url:
        return item.url
    if item.b64_json:
        return f"data:image/png;base64,{item.b64_json}"
    return None


def _friendly_error(exc: Exception | None, tried_models: list[str]) -> str | None:
    if exc is None:
        return None
    models = ", ".join(tried_models)
    if _is_invalid_model_error(exc):
        return (
            f"OpenAI image generation failed for models: {models}. "
            "Run `willbe-trends test-image-gen` to diagnose. "
            "Use the text prompt with your own salon photo meanwhile."
        )
    return (
        "Image could not be generated. Run `willbe-trends test-image-gen` to diagnose, "
        "or use the prompt with your own salon photo."
    )


class OpenAIImageGenerator(ImageGenerator):
    name = "openai"

    def __init__(self, settings: Settings) -> None:
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required for OpenAI image generation.")
        self._client = AsyncOpenAI(api_key=settings.openai_api_key)
        self._model = settings.openai_image_model

    async def generate(self, *, prompt: str, aspect_ratio: str) -> ImageGenerationResult:
        tried: list[str] = []
        last_exc: Exception | None = None
        for model in _models_to_try(self._model):
            tried.append(model)
            try:
                kwargs: dict = {
                    "model": model,
                    "prompt": prompt,
                    "size": _size_for_aspect(aspect_ratio),
                    "n": 1,
                }
                if _is_gpt_image_model(model):
                    kwargs["quality"] = "medium"
                response = await self._client.images.generate(**kwargs)
                url = _image_url_from_response(response)
                if url:
                    return ImageGenerationResult(
                        url=url,
                        provider=self.name,
                        model=model,
                        status="generated",
                    )
                last_exc = RuntimeError("Image API returned no image data.")
            except Exception as exc:  # noqa: BLE001
                last_exc = exc
                if _is_invalid_model_error(exc):
                    continue
                break

        return ImageGenerationResult(
            url=None,
            provider=self.name,
            model=self._model,
            status="failed",
            error=_friendly_error(last_exc, tried),
        )
