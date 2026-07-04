from willbe_trends.config import LLMProviderName, Settings, get_settings
from willbe_trends.llm.anthropic_provider import AnthropicProvider
from willbe_trends.llm.base import LLMProvider
from willbe_trends.llm.ollama_provider import OllamaProvider
from willbe_trends.llm.openai_provider import OpenAIProvider

PROVIDER_FACTORIES: dict[str, type[LLMProvider]] = {
    OpenAIProvider.name: OpenAIProvider,
    AnthropicProvider.name: AnthropicProvider,
    OllamaProvider.name: OllamaProvider,
}


def list_providers() -> list[str]:
    return sorted(PROVIDER_FACTORIES.keys())


def create_provider(
    provider: LLMProviderName | None = None,
    settings: Settings | None = None,
) -> LLMProvider:
    resolved_settings = settings or get_settings()
    provider_name = provider or resolved_settings.willbe_llm_provider

    factory = PROVIDER_FACTORIES.get(provider_name)
    if factory is None:
        supported = ", ".join(list_providers())
        raise ValueError(
            f"Unknown LLM provider '{provider_name}'. Supported: {supported}"
        )

    return factory(resolved_settings)
