from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional
from pydantic import BaseModel


@dataclass
class LLMUsage:
    input_tokens: int
    output_tokens: int
    total_tokens: int
    estimated_cost: float


class LLMMessage(BaseModel):
    role: str
    content: str


class LLMResponse(BaseModel):
    content: str
    usage: LLMUsage
    model: str
    provider: str
    finish_reason: Optional[str] = None


class LLMProvider(ABC):
    @abstractmethod
    async def generate(
        self,
        messages: list[LLMMessage],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs,
    ) -> LLMResponse:
        pass

    @abstractmethod
    async def generate_structured(
        self,
        messages: list[LLMMessage],
        response_model: type[BaseModel],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs,
    ) -> BaseModel:
        pass

    @abstractmethod
    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        pass

    @property
    @abstractmethod
    def default_model(self) -> str:
        pass