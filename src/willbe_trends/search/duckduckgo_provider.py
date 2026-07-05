import asyncio

from ddgs import DDGS

from willbe_trends.config import Settings
from willbe_trends.search.base import RawImageHit, RawSearchHit, SearchProvider


class DuckDuckGoProvider(SearchProvider):
    name = "duckduckgo"

    def __init__(self, settings: Settings | None = None) -> None:
        del settings  # unused; kept for factory parity

    async def search(self, query: str, *, max_results: int = 5) -> list[RawSearchHit]:
        def _run() -> list[RawSearchHit]:
            with DDGS() as ddgs:
                rows = ddgs.text(query, max_results=max_results)
            hits: list[RawSearchHit] = []
            for row in rows:
                hits.append(
                    RawSearchHit(
                        title=row.get("title", "").strip(),
                        url=row.get("href", row.get("url", "")).strip(),
                        snippet=row.get("body", row.get("snippet", "")).strip(),
                    )
                )
            return hits

        return await asyncio.to_thread(_run)

    async def search_images(self, query: str, *, max_results: int = 3) -> list[RawImageHit]:
        def _run() -> list[RawImageHit]:
            with DDGS() as ddgs:
                rows = ddgs.images(query, max_results=max_results)
            hits: list[RawImageHit] = []
            for row in rows:
                image_url = (row.get("image") or row.get("thumbnail") or "").strip()
                if not image_url.startswith("http"):
                    continue
                hits.append(
                    RawImageHit(
                        image_url=image_url,
                        source_url=(row.get("url") or row.get("source") or "").strip(),
                        title=(row.get("title") or query).strip(),
                        thumbnail_url=(row.get("thumbnail") or "").strip(),
                    )
                )
            return hits

        return await asyncio.to_thread(_run)
