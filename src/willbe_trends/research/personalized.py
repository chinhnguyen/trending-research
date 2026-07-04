from willbe_trends.llm.base import LLMProvider
from willbe_trends.models.preferences import UserPreferences
from willbe_trends.models.trends import TrendCategory, TrendReport
from willbe_trends.research.neutral import PERSONALIZED_SYSTEM_PROMPT, build_trend_report


async def research_personalized_trends(
    *,
    category: TrendCategory,
    preferences: UserPreferences,
    llm: LLMProvider,
    region: str = "global",
) -> TrendReport:
    user_prompt = (
        f"Category: {category.value}\n"
        f"Region: {region}\n"
        f"User profile JSON:\n{preferences.model_dump_json(indent=2)}\n\n"
        "Recommend trends this user is likely to enjoy. "
        "Explain the fit in summary and trend descriptions."
    )
    response = await llm.complete(system=PERSONALIZED_SYSTEM_PROMPT, user=user_prompt)
    return build_trend_report(
        category=category,
        mode="personalized",
        llm_response_text=response.content,
        provider=response.provider,
        model=response.model,
    )
