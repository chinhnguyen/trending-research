from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

LLMProviderName = Literal["openai", "anthropic", "ollama"]
SearchProviderName = Literal["duckduckgo", "tavily"]
SocialPlatformName = Literal["instagram", "tiktok"]
PostFormatName = Literal["image", "video"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    willbe_llm_provider: LLMProviderName = Field(
        default="openai",
        validation_alias="WILLBE_LLM_PROVIDER",
    )

    willbe_web_search_enabled: bool = Field(
        default=True,
        validation_alias="WILLBE_WEB_SEARCH_ENABLED",
    )
    willbe_search_provider: SearchProviderName = Field(
        default="duckduckgo",
        validation_alias="WILLBE_SEARCH_PROVIDER",
    )
    willbe_preferred_sources_path: Path = Field(
        default=Path("config/preferred_sources.yaml"),
        validation_alias="WILLBE_PREFERRED_SOURCES_PATH",
    )
    willbe_prompts_path: Path = Field(
        default=Path("config/prompts.yaml"),
        validation_alias="WILLBE_PROMPTS_PATH",
    )
    willbe_search_max_results_per_query: int = Field(
        default=4,
        validation_alias="WILLBE_SEARCH_MAX_RESULTS_PER_QUERY",
    )
    willbe_search_max_citations: int = Field(
        default=10,
        validation_alias="WILLBE_SEARCH_MAX_CITATIONS",
    )
    willbe_image_search_enabled: bool = Field(
        default=True,
        validation_alias="WILLBE_IMAGE_SEARCH_ENABLED",
    )
    willbe_image_search_max_results: int = Field(
        default=3,
        validation_alias="WILLBE_IMAGE_SEARCH_MAX_RESULTS",
    )

    willbe_media_generation_enabled: bool = Field(
        default=False,
        validation_alias="WILLBE_MEDIA_GENERATION_ENABLED",
    )
    willbe_media_require_probe: bool = Field(
        default=True,
        validation_alias="WILLBE_MEDIA_REQUIRE_PROBE",
    )
    willbe_image_generation_provider: Literal["openai", "none"] = Field(
        default="openai",
        validation_alias="WILLBE_IMAGE_GENERATION_PROVIDER",
    )
    willbe_video_generation_provider: Literal["openai", "none"] = Field(
        default="openai",
        validation_alias="WILLBE_VIDEO_GENERATION_PROVIDER",
    )
    willbe_media_max_images_per_post: int = Field(
        default=1,
        validation_alias="WILLBE_MEDIA_MAX_IMAGES_PER_POST",
    )
    willbe_media_max_video_scenes: int = Field(
        default=2,
        validation_alias="WILLBE_MEDIA_MAX_VIDEO_SCENES",
    )
    willbe_media_max_videos_per_post: int = Field(
        default=1,
        validation_alias="WILLBE_MEDIA_MAX_VIDEOS_PER_POST",
    )
    openai_image_model: str = Field(default="gpt-image-1-mini", validation_alias="OPENAI_IMAGE_MODEL")
    openai_video_model: str = Field(default="sora-2", validation_alias="OPENAI_VIDEO_MODEL")

    tavily_api_key: str | None = Field(default=None, validation_alias="TAVILY_API_KEY")

    openai_api_key: str | None = Field(default=None, validation_alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o-mini", validation_alias="OPENAI_MODEL")

    anthropic_api_key: str | None = Field(
        default=None, validation_alias="ANTHROPIC_API_KEY"
    )
    anthropic_model: str = Field(
        default="claude-sonnet-4-20250514",
        validation_alias="ANTHROPIC_MODEL",
    )

    ollama_base_url: str = Field(
        default="http://localhost:11434",
        validation_alias="OLLAMA_BASE_URL",
    )
    ollama_model: str = Field(default="llama3.2", validation_alias="OLLAMA_MODEL")

    willbe_database_url: str = Field(
        default="sqlite:///./data/willbe.db",
        validation_alias="WILLBE_DATABASE_URL",
    )
    willbe_api_host: str = Field(default="127.0.0.1", validation_alias="WILLBE_API_HOST")
    willbe_api_port: int = Field(default=8000, validation_alias="WILLBE_API_PORT")
    willbe_cors_origins: str = Field(
        default="http://localhost:5173,http://127.0.0.1:5173",
        validation_alias="WILLBE_CORS_ORIGINS",
    )
    willbe_http_auth_user: str | None = Field(
        default=None,
        validation_alias="WILLBE_HTTP_AUTH_USER",
    )
    willbe_http_auth_password: str | None = Field(
        default=None,
        validation_alias="WILLBE_HTTP_AUTH_PASSWORD",
    )

    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.willbe_cors_origins.split(",") if origin.strip()]

    def http_auth_enabled(self) -> bool:
        return bool(self.willbe_http_auth_user and self.willbe_http_auth_password)


@lru_cache
def get_settings() -> Settings:
    return Settings()
