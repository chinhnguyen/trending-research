import json
import re
from datetime import datetime, timezone

from willbe_trends.llm.base import LLMProvider
from willbe_trends.models.trends import TrendCategory, TrendReport, TrendSignal


def _extract_json_payload(text: str) -> dict:
    """Parse JSON from a model response, tolerating markdown fences."""
    stripped = text.strip()
    fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", stripped)
    candidate = fence_match.group(1).strip() if fence_match else stripped

    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        start = candidate.find("{")
        end = candidate.rfind("}")
        if start == -1 or end == -1:
            raise ValueError("Model response did not contain valid JSON.") from None
        return json.loads(candidate[start : end + 1])


def build_trend_report(
    *,
    category: TrendCategory,
    mode: str,
    llm_response_text: str,
    provider: str,
    model: str,
) -> TrendReport:
    payload = _extract_json_payload(llm_response_text)

    trends = [TrendSignal.model_validate(item) for item in payload.get("trends", [])]
    summary = payload.get("summary", "").strip()
    if not summary:
        raise ValueError("Model response missing required 'summary' field.")

    return TrendReport(
        category=category,
        mode=mode,
        summary=summary,
        trends=trends,
        generated_at=datetime.now(timezone.utc).isoformat(),
        llm_provider=provider,
        llm_model=model,
    )


NEUTRAL_SYSTEM_PROMPT = """You are a beauty trend researcher focused on objective, widely observable signals.
Return ONLY valid JSON with this shape:
{
  "summary": "2-3 sentence overview of the current nail landscape",
  "trends": [
    {
      "name": "string",
      "description": "string",
      "popularity": "rising|peak|steady|niche",
      "colors": ["string"],
      "techniques": ["string"],
      "tags": ["string"],
      "confidence": 0.0-1.0,
      "source_hint": "string"
    }
  ]
}
Rules:
- Stay neutral: no personalization, no brand endorsements.
- Ground trends in what is broadly visible across social, salons, and editorial.
- Provide 5-8 distinct trends.
- Prefer specificity over generic advice."""


PERSONALIZED_SYSTEM_PROMPT = """You are a nail trend curator producing "you may like it" recommendations.
Return ONLY valid JSON with the same schema as neutral research:
{
  "summary": "warm, concise intro explaining why these picks fit the user",
  "trends": [ ... same trend objects ... ]
}
Rules:
- Respect avoided colors and stated constraints.
- Weight recommendations toward the user's palette, shapes, finishes, and style keywords.
- Still cite real, current nail trends — do not invent fantasy styles.
- Provide 4-6 tailored trends.
- In each trend description, briefly note why it matches the user."""


async def research_neutral_trends(
    *,
    category: TrendCategory,
    llm: LLMProvider,
    region: str = "global",
) -> TrendReport:
    user_prompt = (
        f"Research current {category.value} trends for a {region} audience. "
        "Focus on colors, shapes, finishes, nail art techniques, and seasonal movement. "
        "Today is mid-2026."
    )
    response = await llm.complete(system=NEUTRAL_SYSTEM_PROMPT, user=user_prompt)
    return build_trend_report(
        category=category,
        mode="neutral",
        llm_response_text=response.content,
        provider=response.provider,
        model=response.model,
    )
