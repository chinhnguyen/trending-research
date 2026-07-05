from pydantic import BaseModel, Field

from willbe_trends.models.category import TrendCategory
from willbe_trends.models.search import WebResearchBundle
from willbe_trends.models.usage import LLMUsageStats


class TrendSignal(BaseModel):
    name: str = Field(description="Short trend name")
    description: str = Field(description="What the trend is and why it matters")
    popularity: str = Field(
        default="steady",
        description="Estimated popularity: rising, peak, steady, or niche",
    )
    colors: list[str] = Field(default_factory=list)
    techniques: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0, default=0.7)
    source_hint: str = Field(
        default="",
        description="Where this trend is commonly seen (social, runway, salons, etc.)",
    )
    image_url: str | None = Field(
        default=None,
        description="Reference photo illustrating the trend",
    )
    image_source_url: str | None = Field(
        default=None,
        description="Page URL where the reference image was found",
    )
    image_alt: str | None = Field(default=None, description="Accessible alt text for image")


class TrendReport(BaseModel):
    category: TrendCategory
    mode: str = Field(description="neutral or personalized")
    research_time: str = Field(description="Time period the research targets, e.g. July 2026")
    summary: str
    trends: list[TrendSignal]
    generated_at: str
    llm_provider: str
    llm_model: str
    llm_usage: LLMUsageStats | None = None
    web_research: WebResearchBundle | None = None
