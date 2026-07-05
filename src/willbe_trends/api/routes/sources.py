from fastapi import APIRouter

from willbe_trends.api.schemas import PreferredSourcesConfigOut
from willbe_trends.models.search import PreferredSourcesConfig
from willbe_trends.search.sources_config import (
    default_sources,
    load_sources,
    reset_sources,
    save_sources,
)

router = APIRouter(tags=["sources"])


@router.get("/sources", response_model=PreferredSourcesConfigOut)
def get_sources():
    return PreferredSourcesConfigOut(config=load_sources(), is_default=_is_default())


@router.put("/sources", response_model=PreferredSourcesConfigOut)
def update_sources(config: PreferredSourcesConfig):
    save_sources(config)
    return PreferredSourcesConfigOut(config=config, is_default=False)


@router.post("/sources/reset", response_model=PreferredSourcesConfigOut)
def restore_default_sources():
    config = reset_sources()
    return PreferredSourcesConfigOut(config=config, is_default=True)


def _is_default() -> bool:
    current = load_sources()
    defaults = default_sources()
    return current.model_dump() == defaults.model_dump()
