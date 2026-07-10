from datetime import datetime

from pydantic import BaseModel, Field

from willbe_trends.models.social import SocialPlatform
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


class PlatformPostReview(BaseModel):
    platform: SocialPlatform
    content_format: str = Field(description="e.g. instagram_reel, instagram_feed, tiktok_video")
    strengths: list[str] = Field(default_factory=list)
    improvements: list[str] = Field(default_factory=list)
    hook: str
    caption: str
    hashtags: list[str] = Field(default_factory=list)
    posting_checklist: list[str] = Field(default_factory=list)
    sound_strategy: str | None = Field(
        default=None,
        description="Trending sound or original audio guidance (TikTok / Reels).",
    )
    cover_tip: str | None = Field(
        default=None,
        description="Cover frame or thumbnail guidance for Reels / TikTok.",
    )


class ImageRecommendation(BaseModel):
    label: str
    aspect_ratio: str = Field(default="1:1", description="1:1, 4:5, or 9:16")
    prompt: str
    hook: str | None = None
    caption: str | None = None
    hashtags: list[str] = Field(default_factory=list)
    generated_url: str | None = None
    generation_status: str = Field(default="prompt_only")
    generation_provider: str | None = None
    generation_model: str | None = None
    generation_error: str | None = None


class VideoScene(BaseModel):
    scene_number: int
    duration_seconds: float | None = None
    visual_prompt: str
    on_screen_text: str | None = None
    voiceover: str | None = None
    generated_frame_url: str | None = None
    generation_status: str = Field(default="prompt_only")
    generation_provider: str | None = None
    generation_model: str | None = None
    generation_error: str | None = None


class VideoRecommendation(BaseModel):
    hook: str
    total_duration_seconds: int = Field(default=15, ge=5, le=60)
    music_mood: str | None = None
    scenes: list[VideoScene] = Field(default_factory=list)


class ContentIdea(BaseModel):
    id: str
    platform: SocialPlatform = "instagram"
    angles: list[str] = Field(default_factory=list)
    captions: list[BriefCaption] = Field(default_factory=list)
    hashtags: list[str] = Field(default_factory=list)
    posting_tip: str | None = None
    product_mapping: ProductServiceTieIn | None = None
    platform_review: PlatformPostReview | None = None
    image_recommendations: list[ImageRecommendation] = Field(default_factory=list)
    video_recommendation: VideoRecommendation | None = None
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
