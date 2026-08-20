from typing import Optional
from app.core.config.settings import settings
from app.core.providers.embedding.base import EmbeddingProvider
from app.core.providers.embedding.gemini import GeminiEmbeddingProvider


class EmbeddingProviderFactory:
    _instance: Optional[EmbeddingProvider] = None

    @classmethod
    def get_provider(cls, provider: Optional[str] = None) -> EmbeddingProvider:
        if cls._instance is not None:
            return cls._instance

        provider_name = provider or settings.EMBEDDING_PROVIDER

        if provider_name == "gemini":
            cls._instance = GeminiEmbeddingProvider(
                api_key=settings.EMBEDDING_API_KEY,
                default_model=settings.EMBEDDING_MODEL,
                dimensions=settings.EMBEDDING_DIMENSIONS,
            )
        else:
            raise ValueError(f"Unsupported embedding provider: {provider_name}")

        return cls._instance

    @classmethod
    def reset(cls) -> None:
        cls._instance = None


def get_embedding_provider() -> EmbeddingProvider:
    return EmbeddingProviderFactory.get_provider()