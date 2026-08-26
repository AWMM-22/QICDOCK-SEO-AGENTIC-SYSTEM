import logging
from typing import Optional

from app.core.config.settings import settings, _is_placeholder
from app.core.providers.image.base import ImageProvider

logger = logging.getLogger(__name__)


def get_image_provider(provider: Optional[str] = None) -> Optional[ImageProvider]:
    provider_name = provider or settings.IMAGE_PROVIDER

    if not provider_name or provider_name == "none":
        return None

    if provider_name == "higgsfield":
        if _is_placeholder(settings.HIGGSFIELD_API_KEY_ID) or _is_placeholder(
            settings.HIGGSFIELD_API_KEY_SECRET
        ):
            logger.warning(
                "HIGGSFIELD credentials not configured - falling back to pollinations"
            )
            return get_image_provider("pollinations")
        from app.core.providers.image.higgsfield import HiggsfieldImageProvider

        return HiggsfieldImageProvider(
            key_id=settings.HIGGSFIELD_API_KEY_ID,
            key_secret=settings.HIGGSFIELD_API_KEY_SECRET,
            endpoint=settings.HIGGSFIELD_IMAGE_ENDPOINT,
            poll_timeout_seconds=settings.VIDEO_POLL_TIMEOUT_SECONDS,
        )

    if provider_name == "pollinations":
        from app.core.providers.image.pollinations import PollinationsImageProvider

        return PollinationsImageProvider()

    raise ValueError(f"Unsupported image provider: {provider_name}")