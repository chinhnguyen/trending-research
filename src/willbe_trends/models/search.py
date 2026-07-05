from pydantic import BaseModel, Field

from willbe_trends.models.category import TrendCategory


class PreferredSource(BaseModel):
    """A trusted source domain to prioritize during web research."""

    name: str
    domain: str = Field(description="Domain without scheme, e.g. allure.com")
    weight: float = Field(default=1.0, ge=0.0, le=10.0)
    categories: list[TrendCategory] = Field(default_factory=list)
    enabled: bool = True


class PreferredSourcesConfig(BaseModel):
    version: int = 1
    sources: list[PreferredSource] = Field(default_factory=list)


class WebCitation(BaseModel):
    title: str
    url: str
    snippet: str
    preferred: bool = False
    source_name: str | None = None
    query: str = ""


class WebResearchBundle(BaseModel):
    enabled: bool = True
    search_provider: str
    queries: list[str] = Field(default_factory=list)
    citations: list[WebCitation] = Field(default_factory=list)
