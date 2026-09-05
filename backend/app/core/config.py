from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    # Multi-Provider LLM Keys
    groq_api_key: str = "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"
    groq_api_key_2: str = "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"
    groq_model: str = "openai/gpt-oss-20b"

    gemini_api_key: str = "AIzaSyAPiZfGXRFP4m8IbYIX_XM9EjlqTrXiMho"
    gemini_model: str = "gemini-3.6-flash"
    gemini_visual_api_key: Optional[str] = None

    openai_api_key: str = "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"
    openai_model: str = "gpt-4o-mini"

    # Image provider
    image_provider_api_key: str = ""
    gemini_image_api_key: Optional[str] = None
    image_model: str = "gpt-image-1"

    # Tavily for web search
    tavily_api_key: str = "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"

    database_url: str = "sqlite:///./data/qicdock.db"

    chroma_persist_directory: str = "./data/chroma"

    redis_enabled: bool = False
    redis_url: str = ""

    postgres_enabled: bool = False

    max_review_retries: int = 2

    queue_poll_interval: int = 2

    app_host: str = "0.0.0.0"
    app_port: int = 8000

    frontend_url: str = "http://localhost:3000"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


settings = Settings()