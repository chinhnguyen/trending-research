from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from willbe_trends.models.briefs import ContentIdea, TrendBrief
from willbe_trends.models.media_jobs import MediaJobStatus
from willbe_trends.config import LLMProviderName, PostFormatName, SearchProviderName, SocialPlatformName
from willbe_trends.models.category import TrendCategory
from willbe_trends.models.preferences import UserPreferences
from willbe_trends.models.prompts import PromptConfig
from willbe_trends.models.search import PreferredSourcesConfig, WebCitation, WebResearchBundle
from willbe_trends.models.trends import TrendReport, TrendSignal
from willbe_trends.models.usage import LLMUsageStats


class ResearchRunRequest(BaseModel):
    category: TrendCategory = TrendCategory.NAILS
    region: str = "global"
    research_time: str | None = Field(
        default=None,
        description="Time period to research, e.g. 'July 2026' or 'Summer 2026'",
    )
    provider: LLMProviderName | None = None
    web_search: bool = True
    search_provider: SearchProviderName | None = None


class PersonalizedResearchRequest(ResearchRunRequest):
    preferences: UserPreferences = Field(default_factory=UserPreferences)


class ResearchListItem(BaseModel):
    id: str
    category: TrendCategory
    mode: Literal["neutral", "personalized"]
    summary: str
    region: str
    research_time: str
    generated_at: datetime
    llm_provider: str
    llm_model: str
    llm_usage: LLMUsageStats | None = None
    web_search_enabled: bool
    trend_count: int
    citation_count: int
    image_count: int = 0
    cover_image_url: str | None = None
    created_at: datetime


class ResearchDetail(BaseModel):
    id: str
    region: str
    research_time: str
    web_search_enabled: bool
    preferences: UserPreferences | None = None
    report: TrendReport


class ResearchListResponse(BaseModel):
    items: list[ResearchListItem]
    total: int


class BriefInitRequest(BaseModel):
    report_id: str
    trend_name: str = Field(description="Trend to open in the post composer.")


class BriefGenerateRequest(BaseModel):
    report_id: str
    trend_name: str | None = Field(
        default=None,
        description="When set, build a post brief for this trend only (primary salon workflow).",
    )
    provider: LLMProviderName | None = None
    platform: SocialPlatformName = Field(
        default="instagram",
        description="Target social network for platform-specific post review and media.",
    )
    post_format: PostFormatName = Field(
        default="image",
        description="Generate a still image post or a short-form video post.",
    )
    max_trends: int = Field(default=8, ge=1, le=12)


class ContentIdeaGenerateRequest(BaseModel):
    brief_item_id: str
    provider: LLMProviderName | None = None
    platform: SocialPlatformName = "instagram"
    post_format: PostFormatName | None = None


class MediaJobOut(MediaJobStatus):
    pass


class BriefOut(TrendBrief):
    active_media_jobs: list[MediaJobOut] = Field(default_factory=list)


class ContentIdeaOut(ContentIdea):
    brief_item_id: str
    active_media_job: MediaJobOut | None = None


class MediaPromptTargetRequest(BaseModel):
    content_idea_id: str
    kind: Literal["image", "video"]
    sequence: int = Field(ge=1)


class MediaPromptAdjustRequest(MediaPromptTargetRequest):
    prompt: str = Field(min_length=1)
    hook: str | None = None
    caption: str | None = None
    hashtags: list[str] | None = None


class MediaPromptRegenerateRequest(MediaPromptTargetRequest):
    field: Literal["prompt", "hook", "caption", "hashtags"] = "prompt"


class MediaPromptActionOut(ContentIdeaOut):
    pass


class PromptConfigOut(BaseModel):
    config: PromptConfig
    is_default: bool


class PreferredSourcesConfigOut(BaseModel):
    config: PreferredSourcesConfig
    is_default: bool


class TrendSignalOut(TrendSignal):
    pass


class WebCitationOut(WebCitation):
    pass


class WebResearchOut(WebResearchBundle):
    pass
