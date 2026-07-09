from datetime import datetime

from pydantic import BaseModel, Field

from willbe_trends.models.trends import TrendSignal
from willbe_trends.models.usage import LLMUsageStats


class BriefCaption(BaseModel):
    locale: str = Field(description="Locale code for the generated caption, e.g. en, fi, vi")
    caption: str
    cta: str | None = None


class ProductServiceTieIn(BaseModel):
    service_suggestion: str
    product_suggestion: str
    rationale: str


class ContentIdea(BaseModel):
    id: str
    angles: list[str] = Field(default_factory=list)
    captions: list[BriefCaption] = Field(default_factory=list)
    hashtags: list[str] = Field(default_factory=list)
    posting_tip: str | None = None
    product_mapping: ProductServiceTieIn | None = None
    generated_at: datetime


class BriefItem(BaseModel):
    id: str
    rank: int
    score: float = Field(ge=0.0, le=1.0)
    evidence_summary: str
    why_now: str
    caveats: str | None = None
    trend: TrendSignal
    content_idea: ContentIdea | None = None


class TrendBrief(BaseModel):
    id: str
    report_id: str
    title: str
    summary: str
    region: str
    research_time: str
    generated_at: datetime
    llm_provider: str
    llm_model: str
    llm_usage: LLMUsageStats | None = None
    items: list[BriefItem] = Field(default_factory=list)
