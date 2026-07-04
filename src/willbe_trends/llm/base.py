from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class LLMResponse:
    content: str
    provider: str
    model: str


class LLMProvider(ABC):
    name: str

    @abstractmethod
    async def complete(self, system: str, user: str) -> LLMResponse:
        """Return the model's text completion for the given prompts."""
