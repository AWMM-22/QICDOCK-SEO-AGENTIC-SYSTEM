import logging
from typing import Optional

from app.core.config.settings import settings, _is_placeholder
from app.core.providers.video.base import VideoProvider

logger = logging.getLogger(__name__)


def get_video_provider(provider: Optional[str] = None) -> Optional[VideoProvider]:
    provider_name = provider or settings.VIDEO_PROVIDER

    if provider_name in (None, "", "none"):
        return None

    if provider_name == "higgsfield":
        if _is_placeholder(settings.HIGGSFIELD_API_KEY_ID) or _is_placeholder(
            settings.HIGGSFIELD_API_KEY_SECRET
        ):
            logger.warning(
                "HIGGSFIELD_API_KEY_ID / HIGGSFIELD_API_KEY_SECRET not configured "
                "- video generation unavailable"
            )
            return None
        from app.core.providers.video.higgsfield import HiggsfieldVideoProvider

        return HiggsfieldVideoProvider(
            key_id=settings.HIGGSFIELD_API_KEY_ID,
            key_secret=settings.HIGGSFIELD_API_KEY_SECRET,
            endpoint=settings.HIGGSFIELD_VIDEO_IMAGE_TO_VIDEO_ENDPOINT,
            poll_timeout_seconds=settings.VIDEO_POLL_TIMEOUT_SECONDS,
        )

    logger.warning("Unsupported video provider: %s", provider_name)
    return None

