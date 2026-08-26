from typing import Optional
from app.core.config.settings import settings
from app.core.providers.llm.base import LLMProvider
from app.core.providers.llm.groq import GroqProvider


class LLMProviderFactory:
    _instance: Optional[LLMProvider] = None

    @classmethod
    def get_provider(cls, provider: Optional[str] = None) -> LLMProvider:
        if cls._instance is not None:
            return cls._instance

        provider_name = provider or settings.LLM_PROVIDER

        if provider_name == "groq":
            cls._instance = GroqProvider(
                api_key=settings.LLM_API_KEY,
                default_model=settings.LLM_MODEL,
            )
        else:
            raise ValueError(f"Unsupported LLM provider: {provider_name}")

        return cls._instance

    @classmethod
    def reset(cls) -> None:
        cls._instance = None


def get_llm_provider() -> LLMProvider:
    return LLMProviderFactory.get_provider()