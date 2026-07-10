import pytest

from willbe_trends.media.openai_images import (
    OpenAIImageGenerator,
    _image_url_from_response,
    _is_invalid_model_error,
    _models_to_try,
)


class _FakeImages:
    def __init__(self, responses: list) -> None:
        self._responses = responses
        self.calls: list[dict] = []

    async def generate(self, **kwargs):
        self.calls.append(kwargs)
        action = self._responses[len(self.calls) - 1]
        if isinstance(action, Exception):
            raise action
        return action


class _FakeClient:
    def __init__(self, images: _FakeImages) -> None:
        self.images = images


def test_invalid_model_error_detection():
    assert _is_invalid_model_error(RuntimeError("The model 'dall-e-3' does not exist."))


def test_models_to_try_prefers_gpt_image_chain():
    models = _models_to_try("gpt-image-1-mini")
    assert models[0] == "gpt-image-1-mini"
    assert "gpt-image-2" in models


def test_image_url_from_b64_response():
    response = type("Resp", (), {"data": [type("Item", (), {"b64_json": "abc123", "url": None})()]})()
    assert _image_url_from_response(response) == "data:image/png;base64,abc123"


@pytest.mark.asyncio
async def test_image_generator_falls_back_across_gpt_models():
    fake_images = _FakeImages(
        [
            RuntimeError("Error code: 400 - model 'gpt-image-2' does not exist"),
            type(
                "Resp",
                (),
                {"data": [type("Item", (), {"b64_json": "pngdata", "url": None})()]},
            )(),
        ]
    )
    from willbe_trends.config import Settings

    generator = OpenAIImageGenerator(Settings(openai_api_key="test-key", openai_image_model="gpt-image-2"))
    generator._model = "gpt-image-2"
    generator._client = _FakeClient(fake_images)

    result = await generator.generate(prompt="chrome nails", aspect_ratio="9:16")

    assert result.status == "generated"
    assert result.model == "gpt-image-1.5"
    assert result.url == "data:image/png;base64,pngdata"
    assert fake_images.calls[0]["quality"] == "medium"
    assert fake_images.calls[0]["size"] == "1024x1536"
