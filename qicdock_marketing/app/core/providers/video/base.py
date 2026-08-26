from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class GeneratedVideoResult:
    data: bytes
    mime_type: str
    model: str
    duration_seconds: Optional[int] = None


class VideoProvider(ABC):
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        duration_seconds: int = 8,
        aspect_ratio: str = "9:16",
        reference_images: Optional[list[bytes]] = None,
    ) -> GeneratedVideoResult:
        """Generate a video.

        reference_images: product/poster images used as the visual starting
        frame so the video features the real product.
        """
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        pass

    @property
    @abstractmethod
    def default_model(self) -> str:
        pass
