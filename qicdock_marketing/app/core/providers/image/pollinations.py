import logging
import asyncio
from typing import Optional
from urllib.parse import quote

import httpx

from app.core.providers.image.base import ImageProvider, GeneratedImageResult

logger = logging.getLogger(__name__)

POLLINATIONS_URL = "https://image.pollinations.ai/prompt/{prompt}"

ASPECT_SIZES = {
    "1:1": (1024, 1024),
    "4:5": (896, 1120),
    "9:16": (720, 1280),
    "16:9": (1280, 720),
}


class PollinationsImageProvider(ImageProvider):
    """Free image generation via Pollinations (FLUX) - no API key required.

    Note: text-to-image only. Product reference photos are described in the
    prompt instead of attached (Higgsfield/Gemini providers accept real refs).
    """

    def __init__(self, model: str = "flux", timeout_seconds: int = 180):
        self.model = model
        self.timeout_seconds = timeout_seconds

    @property
    def provider_name(self) -> str:
        return "pollinations"

    @property
    def default_model(self) -> str:
        return self.model

    async def generate(
        self,
        prompt: str,
        aspect_ratio: str = "1:1",
        reference_images: Optional[list[bytes]] = None,
    ) -> GeneratedImageResult:
        if reference_images:
            logger.info(
                "Pollinations is text-only - reference photos cannot be attached "
                "(switch to higgsfield/gemini provider for photo-faithful output)"
            )

        width, height = ASPECT_SIZES.get(aspect_ratio, (896, 1120))

        # Pollinations rejects very long prompt URLs (404) - truncate hard,
        # retry with an even shorter core if the first attempt 404s.
        full_prompt = prompt.strip()
        core_prompt = " ".join(full_prompt.split()[:90])  # ~600 chars

        last_error = None
        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            for attempt, prompt_text in enumerate([full_prompt, core_prompt, core_prompt]):
                url = (
                    f"{POLLINATIONS_URL.format(prompt=quote(prompt_text[:1500]))}"
                    f"?width={width}&height={height}&model={self.model}"
                    f"&nologo=true&enhance=false&safe=false&seed={42 + attempt}"
                )
                try:
                    resp = await client.get(url)
                    if resp.status_code == 200 and resp.content[:4] != b"<html":
                        return GeneratedImageResult(
                            data=resp.content,
                            mime_type="image/jpeg",
                            model=self.model,
                        )
                    last_error = f"HTTP {resp.status_code}: {resp.text[:150]}"
                except Exception as e:
                    last_error = str(e)
                await asyncio.sleep(5 * (attempt + 1))

        raise ValueError(f"Pollinations generation failed after retries: {last_error}")
