from functools import lru_cache
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    APP_NAME: str = "Qicdock AI Marketing Team"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/qicdock_marketing",
        description="PostgreSQL async connection URL"
    )
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20

    REDIS_URL: Optional[str] = Field(
        default=None,
        description="Redis connection URL for caching/queue"
    )

    LLM_PROVIDER: str = Field(
        default="gemini",
        description="LLM provider: gemini, openai, anthropic, local"
    )
    LLM_MODEL: str = Field(
        default="gemini-1.5-pro",
        description="LLM model name"
    )
    LLM_API_KEY: Optional[str] = Field(
        default=None,
        description="LLM API key"
    )
    LLM_TEMPERATURE: float = 0.7
    LLM_MAX_TOKENS: int = 4096

    EMBEDDING_PROVIDER: str = Field(
        default="gemini",
        description="Embedding provider: gemini, openai, local"
    )
    EMBEDDING_MODEL: str = Field(
        default="text-embedding-004",
        description="Embedding model name"
    )
    EMBEDDING_API_KEY: Optional[str] = Field(
        default=None,
        description="Embedding API key"
    )
    EMBEDDING_DIMENSIONS: int = 768

    SEARCH_PROVIDER: str = Field(
        default="tavily",
        description="Search provider: tavily, serper, duckduckgo"
    )
    SEARCH_API_KEY: Optional[str] = Field(
        default=None,
        description="Search API key"
    )

    IMAGE_PROVIDER: str = Field(
        default="gemini",
        description="Image provider: gemini, openai, stability, replicate"
    )
    IMAGE_MODEL: str = Field(
        default="gemini-2.0-flash-exp-image-generation",
        description="Image generation model"
    )
    IMAGE_API_KEY: Optional[str] = Field(
        default=None,
        description="Image generation API key"
    )

    EMAIL_PROVIDER: str = Field(
        default="resend",
        description="Email provider: resend, sendgrid, smtp"
    )
    EMAIL_FROM: str = Field(
        default="marketing@qicdock.com",
        description="From email address"
    )
    EMAIL_TO: str = Field(
        default="founder@qicdock.com",
        description="Default recipient email"
    )
    EMAIL_API_KEY: Optional[str] = Field(
        default=None,
        description="Email provider API key"
    )
    SMTP_HOST: Optional[str] = Field(
        default=None,
        description="SMTP host"
    )
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = Field(
        default=None,
        description="SMTP username"
    )
    SMTP_PASSWORD: Optional[str] = Field(
        default=None,
        description="SMTP password"
    )
    SMTP_TLS: bool = True

    LANGSMITH_API_KEY: Optional[str] = Field(
        default=None,
        description="LangSmith API key for observability"
    )
    LANGSMITH_PROJECT: str = "qicdock-marketing"
    LANGSMITH_TRACING: bool = False

    SECRET_KEY: str = Field(
        default="dev-secret-key-change-in-production",
        description="Secret key for JWT/session"
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    API_V1_PREFIX: str = "/api/v1"
    CORS_ORIGINS: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        description="Allowed CORS origins"
    )

    MAX_REVISION_LOOPS: int = 2
    MAX_IMAGE_REGENERATION_ATTEMPTS: int = 2

    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()