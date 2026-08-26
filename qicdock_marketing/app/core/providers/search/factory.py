import logging
from typing import Optional

from app.core.config.settings import settings
from app.core.providers.search.base import SearchProvider

logger = logging.getLogger(__name__)


def get_search_provider(provider: Optional[str] = None) -> Optional[SearchProvider]:
    provider_name = provider or settings.SEARCH_PROVIDER

    if not settings.SEARCH_API_KEY:
        logger.warning("SEARCH_API_KEY not configured - external research disabled")
        return None

    if provider_name == "tavily":
        from app.core.providers.search.tavily import TavilySearchProvider

        return TavilySearchProvider(api_key=settings.SEARCH_API_KEY)

    raise ValueError(f"Unsupported search provider: {provider_name}")
