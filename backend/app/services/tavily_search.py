import httpx
import logging
from typing import List, Dict, Any, Optional
from app.core.config import settings

logger = logging.getLogger(__name__)


class TavilySearchService:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.tavily_api_key
        self.base_url = "https://api.tavily.com"
        self.client = httpx.Client(timeout=30.0) if self.api_key else None

    def search(self, query: str, max_results: int = 5, search_depth: str = "basic") -> List[Dict[str, Any]]:
        """Search the web using Tavily"""
        if not self.client:
            logger.warning("Tavily API key not configured, returning empty results")
            return []

        try:
            response = self.client.post(
                f"{self.base_url}/search",
                headers={"Content-Type": "application/json"},
                json={
                    "api_key": self.api_key,
                    "query": query,
                    "max_results": max_results,
                    "search_depth": search_depth,
                    "include_answer": True,
                    "include_raw_content": False,
                },
            )
            response.raise_for_status()
            data = response.json()
            return data.get("results", [])
        except Exception as e:
            logger.error(f"Tavily search failed: {e}")
            return []

    def search_competitors(self, brand: str, industry: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """Search for competitor information"""
        query = f"{brand} competitors {industry} India marketing strategy 2024"
        return self.search(query, max_results=max_results, search_depth="advanced")

    def search_trends(self, topic: str, platform: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """Search for current trends on a platform"""
        query = f"{topic} trends {platform} India 2024 marketing"
        return self.search(query, max_results=max_results, search_depth="basic")

    def search_festival_relevance(self, festival: str, brand: str, industry: str) -> List[Dict[str, Any]]:
        """Search if a festival is relevant for a brand"""
        query = f"{festival} marketing {brand} {industry} India campaign examples"
        return self.search(query, max_results=3, search_depth="basic")

    def search_content_gaps(self, brand: str, industry: str, audience: str) -> List[Dict[str, Any]]:
        """Search for content gaps in the industry"""
        query = f"{industry} content marketing gaps {audience} India {brand}"
        return self.search(query, max_results=5, search_depth="advanced")


_tavily_instance: Optional[TavilySearchService] = None


def get_tavily_search() -> TavilySearchService:
    global _tavily_instance
    if _tavily_instance is None:
        _tavily_instance = TavilySearchService()
    return _tavily_instance