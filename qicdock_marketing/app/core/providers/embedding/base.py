from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional
from pydantic import BaseModel


@dataclass
class EmbeddingUsage:
    input_tokens: int
    estimated_cost: float


class EmbeddingResponse(BaseModel):
    embeddings: list[list[float]]
    usage: EmbeddingUsage
    model: str
    provider: str


class EmbeddingProvider(ABC):
    @abstractmethod
    async def embed(
        self,
        texts: list[str],
        model: Optional[str] = None,
        **kwargs,
    ) -> EmbeddingResponse:
        pass

    @abstractmethod
    async def embed_query(self, text: str, model: Optional[str] = None) -> list[float]:
        pass

    @abstractmethod
    def estimate_cost(self, input_tokens: int) -> float:
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        pass

    @property
    @abstractmethod
    def default_model(self) -> str:
        pass

    @property
    @abstractmethod
    def dimensions(self) -> int:
        pass