from openai import AsyncOpenAI

from willbe_trends.config import Settings
from willbe_trends.llm.base import LLMProvider, LLMResponse
from willbe_trends.llm.pricing import estimate_cost_usd
from willbe_trends.models.usage import LLMUsageStats


class OpenAIProvider(LLMProvider):
    name = "openai"

    def __init__(self, settings: Settings) -> None:
        if not settings.openai_api_key:
            raise ValueError(
                "OPENAI_API_KEY is required when using the openai provider."
            )
        self._client = AsyncOpenAI(api_key=settings.openai_api_key)
        self._model = settings.openai_model

    async def complete(self, system: str, user: str) -> LLMResponse:
        response = await self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0.4,
        )
        content = response.choices[0].message.content or ""
        usage = response.usage
        stats = None
        if usage is not None:
            stats = LLMUsageStats(
                prompt_tokens=usage.prompt_tokens or 0,
                completion_tokens=usage.completion_tokens or 0,
                total_tokens=usage.total_tokens or 0,
                estimated_cost_usd=estimate_cost_usd(
                    self._model,
                    prompt_tokens=usage.prompt_tokens or 0,
                    completion_tokens=usage.completion_tokens or 0,
                ),
            )
        return LLMResponse(content=content, provider=self.name, model=self._model, usage=stats)
