import os
import json
from typing import Optional, Type
from pydantic import BaseModel
import google.generativeai as genai
from google.generativeai.types import GenerationConfig
from app.core.providers.llm.base import (
    LLMProvider,
    LLMMessage,
    LLMResponse,
    LLMUsage,
)


GEMINI_PRICING = {
    "gemini-1.5-pro": {"input": 0.0035, "output": 0.0105},
    "gemini-1.5-flash": {"input": 0.00035, "output": 0.00105},
    "gemini-2.0-flash-exp": {"input": 0.00015, "output": 0.0006},
    "gemini-2.0-flash-exp-image-generation": {"input": 0.00015, "output": 0.0006},
}


class GeminiProvider(LLMProvider):
    def __init__(
        self,
        api_key: Optional[str] = None,
        default_model: str = "gemini-1.5-pro",
    ):
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY") or os.getenv("LLM_API_KEY")
        if not self.api_key:
            raise ValueError("Gemini API key not provided")
        genai.configure(api_key=self.api_key)
        self._default_model = default_model

    @property
    def provider_name(self) -> str:
        return "gemini"

    @property
    def default_model(self) -> str:
        return self._default_model

    def _convert_messages(self, messages: list[LLMMessage]) -> list[dict]:
        return [{"role": msg.role, "parts": [msg.content]} for msg in messages]

    def _get_pricing(self, model: str) -> dict:
        return GEMINI_PRICING.get(model, {"input": 0.0, "output": 0.0})

    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        pricing = self._get_pricing(self._default_model)
        return (input_tokens * pricing["input"] + output_tokens * pricing["output"]) / 1000

    async def generate(
        self,
        messages: list[LLMMessage],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs,
    ) -> LLMResponse:
        model_name = model or self._default_model
        gemini_model = genai.GenerativeModel(model_name)

        config = GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
        )

        response = await gemini_model.generate_content_async(
            self._convert_messages(messages),
            generation_config=config,
        )

        usage = LLMUsage(
            input_tokens=response.usage_metadata.prompt_token_count if response.usage_metadata else 0,
            output_tokens=response.usage_metadata.candidates_token_count if response.usage_metadata else 0,
            total_tokens=response.usage_metadata.total_token_count if response.usage_metadata else 0,
            estimated_cost=0.0,
        )
        usage.estimated_cost = self.estimate_cost(usage.input_tokens, usage.output_tokens)

        return LLMResponse(
            content=response.text or "",
            usage=usage,
            model=model_name,
            provider=self.provider_name,
            finish_reason=str(response.candidates[0].finish_reason) if response.candidates else None,
        )

    async def generate_structured(
        self,
        messages: list[LLMMessage],
        response_model: Type[BaseModel],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs,
    ) -> BaseModel:
        model_name = model or self._default_model
        gemini_model = genai.GenerativeModel(model_name)

        schema = response_model.model_json_schema()
        schema_str = json.dumps(schema, indent=2)

        structured_prompt = (
            f"Output a valid JSON object that conforms to this schema:\n{schema_str}\n\n"
            f"Respond ONLY with the JSON object, no additional text."
        )

        structured_messages = messages + [LLMMessage(role="user", content=structured_prompt)]

        config = GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
            response_mime_type="application/json",
        )

        response = await gemini_model.generate_content_async(
            self._convert_messages(structured_messages),
            generation_config=config,
        )

        usage = LLMUsage(
            input_tokens=response.usage_metadata.prompt_token_count if response.usage_metadata else 0,
            output_tokens=response.usage_metadata.candidates_token_count if response.usage_metadata else 0,
            total_tokens=response.usage_metadata.total_token_count if response.usage_metadata else 0,
            estimated_cost=0.0,
        )
        usage.estimated_cost = self.estimate_cost(usage.input_tokens, usage.output_tokens)

        try:
            parsed = json.loads(response.text or "{}")
            return response_model(**parsed)
        except Exception as e:
            raise ValueError(f"Failed to parse structured response: {e}") from e