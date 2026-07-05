from fastapi import APIRouter

from willbe_trends.api.schemas import PromptConfigOut
from willbe_trends.models.prompts import PromptConfig
from willbe_trends.research.prompts_config import default_prompts, load_prompts, reset_prompts, save_prompts

router = APIRouter(tags=["prompts"])


@router.get("/prompts", response_model=PromptConfigOut)
def get_prompts():
    return PromptConfigOut(config=load_prompts(), is_default=_is_default())


@router.put("/prompts", response_model=PromptConfigOut)
def update_prompts(config: PromptConfig):
    save_prompts(config)
    return PromptConfigOut(config=config, is_default=False)


@router.post("/prompts/reset", response_model=PromptConfigOut)
def restore_default_prompts():
    config = reset_prompts()
    return PromptConfigOut(config=config, is_default=True)


def _is_default() -> bool:
    current = load_prompts()
    defaults = default_prompts()
    return current.model_dump() == defaults.model_dump()
