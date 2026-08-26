import logging
from typing import Optional

import httpx

from app.core.providers.search.base import SearchProvider, SearchResult

logger = logging.getLogger(__name__)

TAVILY_SEARCH_URL = "https://api.tavily.com/search"


class TavilySearchProvider(SearchProvider):
    def __init__(self, api_key: str):
        self.api_key = api_key

    @property
    def provider_name(self) -> str:
        return "tavily"

    async def search(self, query: str, max_results: int = 5) -> list[SearchResult]:
        payload = {
            "api_key": self.api_key,
            "query": query,
            "max_results": max_results,
            "include_answer": False,
        }
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(TAVILY_SEARCH_URL, json=payload)
                resp.raise_for_status()
                data = resp.json()
        except Exception as e:
            logger.warning("Tavily search failed for query %r: %s", query, e)
            return []

        results = []
        for item in data.get("results", []):
            results.append(
                SearchResult(
                    title=item.get("title", ""),
                    url=item.get("url", ""),
                    snippet=item.get("content", "")[:1000],
                    source="web",
                )
            )
        return results
