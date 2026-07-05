from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class RawSearchHit:
    title: str
    url: str
    snippet: str


@dataclass(frozen=True)
class RawImageHit:
    image_url: str
    source_url: str
    title: str
    thumbnail_url: str = ""


class SearchProvider(ABC):
    name: str

    @abstractmethod
    async def search(self, query: str, *, max_results: int = 5) -> list[RawSearchHit]:
        """Return normalized web search hits for a query."""

    async def search_images(
        self, query: str, *, max_results: int = 3
    ) -> list[RawImageHit]:
        """Return image hits for a query. Override in providers that support images."""
        del query, max_results
        return []
