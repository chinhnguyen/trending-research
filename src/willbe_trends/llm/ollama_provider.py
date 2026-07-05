import httpx

from willbe_trends.config import Settings
from willbe_trends.llm.base import LLMProvider, LLMResponse
from willbe_trends.models.usage import LLMUsageStats


class OllamaProvider(LLMProvider):
    name = "ollama"

    def __init__(self, settings: Settings) -> None:
        self._base_url = settings.ollama_base_url.rstrip("/")
        self._model = settings.ollama_model

    async def complete(self, system: str, user: str) -> LLMResponse:
        payload = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "stream": False,
            "options": {"temperature": 0.4},
        }
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self._base_url}/api/chat",
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

        content = data.get("message", {}).get("content", "")
        prompt_tokens = int(data.get("prompt_eval_count") or 0)
        completion_tokens = int(data.get("eval_count") or 0)
        stats = LLMUsageStats(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            estimated_cost_usd=0.0,
        )
        return LLMResponse(
            content=content,
            provider=self.name,
            model=self._model,
            usage=stats,
        )
