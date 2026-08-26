from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class GeneratedImageResult:
    data: bytes
    mime_type: str
    model: str


class ImageProvider(ABC):
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        aspect_ratio: str = "1:1",
        reference_images: Optional[list[bytes]] = None,
    ) -> GeneratedImageResult:
        """Generate an image.

        reference_images: raw bytes of product photos the model should use
        as visual ground truth so the actual product appears in the output.
        """
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        pass
