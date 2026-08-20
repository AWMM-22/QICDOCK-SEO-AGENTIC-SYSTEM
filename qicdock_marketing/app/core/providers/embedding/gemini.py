import os
from typing import Optional
import google.generativeai as genai
from app.core.providers.embedding.base import (
    EmbeddingProvider,
    EmbeddingResponse,
    EmbeddingUsage,
)


GEMINI_EMBEDDING_PRICING = {
    "text-embedding-004": 0.00002,
}


class GeminiEmbeddingProvider(EmbeddingProvider):
    def __init__(
        self,
        api_key: Optional[str] = None,
        default_model: str = "text-embedding-004",
        dimensions: int = 768,
    ):
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY") or os.getenv("EMBEDDING_API_KEY")
        if not self.api_key:
            raise ValueError("Gemini API key not provided")
        genai.configure(api_key=self.api_key)
        self._default_model = default_model
        self._dimensions = dimensions

    @property
    def provider_name(self) -> str:
        return "gemini"

    @property
    def default_model(self) -> str:
        return self._default_model

    @property
    def dimensions(self) -> int:
        return self._dimensions

    def _get_pricing(self, model: str) -> float:
        return GEMINI_EMBEDDING_PRICING.get(model, 0.0)

    def estimate_cost(self, input_tokens: int) -> float:
        pricing = self._get_pricing(self._default_model)
        return (input_tokens * pricing) / 1000

    async def embed(
        self,
        texts: list[str],
        model: Optional[str] = None,
        **kwargs,
    ) -> EmbeddingResponse:
        model_name = model or self._default_model
        embeddings = []

        total_tokens = 0
        for text in texts:
            result = await genai.embed_content_async(
                model=model_name,
                content=text,
                task_type="retrieval_document",
            )
            embeddings.append(result["embedding"])
            total_tokens += len(text) // 4

        usage = EmbeddingUsage(
            input_tokens=total_tokens,
            estimated_cost=self.estimate_cost(total_tokens),
        )

        return EmbeddingResponse(
            embeddings=embeddings,
            usage=usage,
            model=model_name,
            provider=self.provider_name,
        )

    async def embed_query(self, text: str, model: Optional[str] = None) -> list[float]:
        model_name = model or self._default_model
        result = await genai.embed_content_async(
            model=model_name,
            content=text,
            task_type="retrieval_query",
        )
        return result["embedding"]