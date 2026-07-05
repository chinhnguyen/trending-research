from anthropic import AsyncAnthropic

from willbe_trends.config import Settings
from willbe_trends.llm.base import LLMProvider, LLMResponse
from willbe_trends.llm.pricing import estimate_cost_usd
from willbe_trends.models.usage import LLMUsageStats


class AnthropicProvider(LLMProvider):
    name = "anthropic"

    def __init__(self, settings: Settings) -> None:
        if not settings.anthropic_api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY is required when using the anthropic provider."
            )
        self._client = AsyncAnthropic(api_key=settings.anthropic_api_key)
        self._model = settings.anthropic_model

    async def complete(self, system: str, user: str) -> LLMResponse:
        response = await self._client.messages.create(
            model=self._model,
            max_tokens=4096,
            system=system,
            messages=[{"role": "user", "content": user}],
            temperature=0.4,
        )
        content = response.content[0].text if response.content else ""
        stats = None
        if response.usage is not None:
            prompt_tokens = response.usage.input_tokens or 0
            completion_tokens = response.usage.output_tokens or 0
            stats = LLMUsageStats(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
                estimated_cost_usd=estimate_cost_usd(
                    self._model,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                ),
            )
        return LLMResponse(content=content, provider=self.name, model=self._model, usage=stats)
