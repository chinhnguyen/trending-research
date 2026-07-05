from pydantic import BaseModel, Field


class LLMUsageStats(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    estimated_cost_usd: float = Field(default=0.0, ge=0.0)
