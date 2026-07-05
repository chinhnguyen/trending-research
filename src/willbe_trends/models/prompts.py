from pydantic import BaseModel, Field


def _default_neutral_system_prompt() -> str:
    from willbe_trends.research.prompt_defaults import NEUTRAL_SYSTEM_PROMPT

    return NEUTRAL_SYSTEM_PROMPT


def _default_personalized_system_prompt() -> str:
    from willbe_trends.research.prompt_defaults import PERSONALIZED_SYSTEM_PROMPT

    return PERSONALIZED_SYSTEM_PROMPT


def _default_web_grounded_rules() -> str:
    from willbe_trends.research.prompt_defaults import WEB_GROUNDED_RULES

    return WEB_GROUNDED_RULES


def _default_neutral_user_template() -> str:
    from willbe_trends.research.prompt_defaults import NEUTRAL_USER_TEMPLATE

    return NEUTRAL_USER_TEMPLATE


def _default_personalized_user_template() -> str:
    from willbe_trends.research.prompt_defaults import PERSONALIZED_USER_TEMPLATE

    return PERSONALIZED_USER_TEMPLATE


class PromptConfig(BaseModel):
    version: int = 1
    neutral_system_prompt: str = Field(default_factory=_default_neutral_system_prompt)
    personalized_system_prompt: str = Field(default_factory=_default_personalized_system_prompt)
    web_grounded_rules: str = Field(default_factory=_default_web_grounded_rules)
    neutral_user_template: str = Field(default_factory=_default_neutral_user_template)
    personalized_user_template: str = Field(default_factory=_default_personalized_user_template)

    def neutral_system(self) -> str:
        return f"{self.neutral_system_prompt.strip()}\n{self.web_grounded_rules.strip()}".strip()

    def personalized_system(self) -> str:
        return f"{self.personalized_system_prompt.strip()}\n{self.web_grounded_rules.strip()}".strip()
