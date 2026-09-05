from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
import logging
import base64
import httpx
from openai import OpenAI

from app.core.config import settings

logger = logging.getLogger(__name__)


class ImageProvider(ABC):
    @abstractmethod
    def generate(self, prompt: str, aspect_ratio: str = "1:1", model: Optional[str] = None, quality: str = "standard", n: int = 1) -> list[str]:
        pass


class OpenAIImageProvider(ImageProvider):
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or settings.image_provider_api_key
        self.model = model or settings.image_model
        self.client = OpenAI(api_key=self.api_key) if self.api_key else None

    def generate(self, prompt: str, aspect_ratio: str = "1:1", model: Optional[str] = None, quality: str = "standard", n: int = 1) -> list[str]:
        if not self.client:
            raise ValueError("Image provider API key not configured")

        used_model = model or self.model
        size_map = {
            "1:1": "1024x1024",
            "16:9": "1792x1024",
            "9:16": "1024x1792",
            "4:3": "1152x896",
            "3:4": "896x1152",
        }
        size = size_map.get(aspect_ratio, "1024x1024")

        response = self.client.images.generate(
            model=used_model,
            prompt=prompt,
            size=size,
            quality=quality,
            n=n,
        )

        return [img.url for img in response.data if img.url]


class GeminiImageProvider(ImageProvider):
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or settings.gemini_image_api_key
        self.model = model or "gemini-3.1-flash-image"
        if self.api_key:
            try:
                from google import genai
                self.client = genai.Client(api_key=self.api_key)
            except ImportError:
                logger.warning("google-genai package not installed")
                self.client = None
        else:
            self.client = None

    def generate(self, prompt: str, aspect_ratio: str = "1:1", model: Optional[str] = None, quality: str = "standard", n: int = 1) -> list[str]:
        if not self.client:
            raise ValueError("Gemini Image API key not configured or google-genai not installed")

        used_model = model or self.model
        config = dict(
            number_of_images=n,
            aspect_ratio=aspect_ratio,
            output_mime_type="image/jpeg"
        )
        try:
            response = self.client.models.generate_content(
                model=used_model,
                contents=prompt,
            )
            urls = []
            if response.candidates and response.candidates[0].content.parts:
                for part in response.candidates[0].content.parts:
                    if part.inline_data:
                        img_b64 = base64.b64encode(part.inline_data.data).decode('utf-8')
                        urls.append(f"data:image/jpeg;base64,{img_b64}")
            return urls
        except Exception as e:
            logger.error(f"Gemini image generation failed: {e}")
            raise


class MockImageProvider(ImageProvider):
    def generate(self, prompt: str, aspect_ratio: str = "1:1", model: Optional[str] = None, quality: str = "standard", n: int = 1) -> list[str]:
        logger.info(f"Mock image generation for prompt: {prompt[:100]}...")
        return ["https://via.placeholder.com/1024x1024?text=Mock+Image"]


def get_image_provider() -> ImageProvider:
    if settings.gemini_image_api_key:
        return GeminiImageProvider()
    if settings.image_provider_api_key:
        return OpenAIImageProvider()
    logger.warning("Image provider API key not configured, using mock provider")
    return MockImageProvider()