from abc import ABC, abstractmethod
from dataclasses import dataclass

from willbe_trends.models.usage import LLMUsageStats


@dataclass(frozen=True)
class LLMResponse:
    content: str
    provider: str
    model: str
    usage: LLMUsageStats | None = None


class LLMProvider(ABC):
    name: str

    @abstractmethod
    async def complete(self, system: str, user: str) -> LLMResponse:
        """Return the model's text completion for the given prompts."""
