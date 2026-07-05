from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from willbe_trends.config import LLMProviderName, SearchProviderName
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
