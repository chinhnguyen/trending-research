from enum import Enum

from pydantic import BaseModel, Field


class TrendCategory(str, Enum):
    NAILS = "nails"


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


class TrendReport(BaseModel):
    category: TrendCategory
    mode: str = Field(description="neutral or personalized")
    summary: str
    trends: list[TrendSignal]
    generated_at: str
    llm_provider: str
    llm_model: str
