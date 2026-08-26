import logging
from typing import Optional

from app.core.providers.higgsfield_client import (
    HiggsfieldClient,
    HiggsfieldError,
)
from app.core.providers.image.base import ImageProvider, GeneratedImageResult

logger = logging.getLogger(__name__)


class HiggsfieldImageProvider(ImageProvider):
    """Image generation via Higgsfield with product-photo references.

    Primary: /nano-banana (multi reference, if enabled on the account)
    Fallback: /higgsfield-ai/soul/reference (single image_reference_url)
    """

    def __init__(
        self,
        key_id: str,
        key_secret: str,
        endpoint: str = "/nano-banana",
        fallback_endpoint: str = "/higgsfield-ai/soul/reference",
        poll_timeout_seconds: int = 600,
    ):
        self.client = HiggsfieldClient(key_id, key_secret, poll_timeout_seconds)
        self.endpoint = endpoint
        self.fallback_endpoint = fallback_endpoint

    @property
    def provider_name(self) -> str:
        return "higgsfield"

    @property
    def default_model(self) -> str:
        return self.endpoint.strip("/").split("/")[-1]

    async def _generate_on(self, endpoint: str, payload: dict) -> GeneratedImageResult:
        submit_response = await self.client.submit(endpoint, payload)
        urls = await self.client.wait_for_result(submit_response)
        data = await self.client.download(urls[0])
        mime_type = "image/png" if ".png" in urls[0].lower() else "image/jpeg"
        return GeneratedImageResult(
            data=data,
            mime_type=mime_type,
            model=endpoint.strip("/").split("/")[-1],
        )

    async def generate(
        self,
        prompt: str,
        aspect_ratio: str = "1:1",
        reference_images: Optional[list[bytes]] = None,
    ) -> GeneratedImageResult:
        ref_urls: list[str] = []
        if reference_images:
            try:
                for img in reference_images[:8]:
                    url = await self.client.upload_image(img)
                    if url:
                        ref_urls.append(url)
            except HiggsfieldError as e:
                logger.warning("Reference image upload failed: %s", e)

        errors: list[str] = []

        # 1. Nano Banana (multi-reference, best fidelity)
        nano_ar_choices = (
            "auto", "1:1", "4:3", "3:4", "3:2", "2:3", "5:4", "4:5", "16:9", "9:16", "21:9"
        )
        try:
            payload: dict = {
                "prompt": prompt[:1800],
                "aspect_ratio": aspect_ratio if aspect_ratio in nano_ar_choices else "4:5",
                "num_images": 1,
                "output_format": "png",
            }
            if ref_urls:
                payload["input_images"] = [
                    {"type": "image_url", "image_url": u} for u in ref_urls[:8]
                ]
            return await self._generate_on(self.endpoint, payload)
        except HiggsfieldError as e:
            errors.append(f"{self.endpoint}: {e}")
            logger.warning("Nano Banana unavailable (%s) - trying Soul reference", e)

        # 2. Soul reference (single reference URL)
        if ref_urls:
            try:
                soul_ar_choices = ("9:16", "16:9", "4:3", "3:4", "1:1", "2:3", "3:2")
                soul_ar = aspect_ratio if aspect_ratio in soul_ar_choices else "3:4"
                payload = {
                    "prompt": prompt[:1800],
                    "aspect_ratio": soul_ar,
                    "image_reference_url": ref_urls[0],
                    "batch_size": 1,
                    "resolution": "1080p",
                    "enhance_prompt": False,
                }
                return await self._generate_on(self.fallback_endpoint, payload)
            except HiggsfieldError as e:
                errors.append(f"{self.fallback_endpoint}: {e}")

        raise HiggsfieldError("; ".join(errors))
