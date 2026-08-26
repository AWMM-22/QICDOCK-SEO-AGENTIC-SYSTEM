import logging
from typing import Optional

from app.core.providers.higgsfield_client import (
    HiggsfieldClient,
    HiggsfieldError,
)
from app.core.providers.video.base import VideoProvider, GeneratedVideoResult

logger = logging.getLogger(__name__)


class HiggsfieldVideoProvider(VideoProvider):
    """Video generation via Higgsfield image-to-video models (Veo 3.1 etc).

    Flow: upload poster/product image -> submit image-to-video job ->
    poll -> download mp4.
    """

    def __init__(
        self,
        key_id: str,
        key_secret: str,
        endpoint: str = "/veo3.1/fast/image-to-video",
        poll_timeout_seconds: int = 900,
    ):
        self.client = HiggsfieldClient(key_id, key_secret, poll_timeout_seconds)
        self.endpoint = endpoint

    @property
    def provider_name(self) -> str:
        return "higgsfield"

    @property
    def default_model(self) -> str:
        return self.endpoint.strip("/").split("/")[-1]

    async def generate(
        self,
        prompt: str,
        duration_seconds: int = 8,
        aspect_ratio: str = "9:16",
        reference_images: Optional[list[bytes]] = None,
    ) -> GeneratedVideoResult:
        payload: dict = {
            "prompt": prompt,
            "aspect_ratio": aspect_ratio,
            "duration": f"{duration_seconds}s"
            if duration_seconds in (4, 6, 8)
            else "8s",
            "resolution": "720p",
        }

        if reference_images:
            try:
                input_images = []
                for img in reference_images[:2]:
                    url = await self.client.upload_image(img)
                    if url:
                        input_images.append({"type": "image_url", "image_url": url})
                if input_images:
                    payload["input_images"] = input_images[:1]
            except HiggsfieldError as e:
                logger.warning("Reference image upload failed for video: %s", e)

        submit_response = await self.client.submit(self.endpoint, payload)
        urls = await self.client.wait_for_result(submit_response)

        data = await self.client.download(urls[0])

        return GeneratedVideoResult(
            data=data,
            mime_type="video/mp4",
            model=self.default_model,
            duration_seconds=duration_seconds,
        )
