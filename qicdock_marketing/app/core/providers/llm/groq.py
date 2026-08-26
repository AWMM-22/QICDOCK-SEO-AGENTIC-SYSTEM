import os
import json
import re
from typing import Optional, Type
from pydantic import BaseModel

import httpx

from app.core.providers.llm.base import (
    LLMProvider,
    LLMMessage,
    LLMResponse,
    LLMUsage,
)


GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

GROQ_PRICING = {
    # USD per 1K tokens (approximate Groq published rates)
    "openai/gpt-oss-120b": {"input": 0.00015, "output": 0.00075},
    "openai/gpt-oss-20b": {"input": 0.00004, "output": 0.00015},
    "qwen/qwen3.6-27b": {"input": 0.00006, "output": 0.00018},
}


class GroqProvider(LLMProvider):
    def __init__(
        self,
        api_key: Optional[str] = None,
        default_model: str = "llama-3.3-70b-versatile",
    ):
        self.api_key = api_key or os.getenv("GROQ_API_KEY") or os.getenv("LLM_API_KEY")
        if not self.api_key:
            raise ValueError("Groq API key not provided")
        self._default_model = default_model

    @property
    def provider_name(self) -> str:
        return "groq"

    @property
    def default_model(self) -> str:
        return self._default_model

    def _convert_messages(self, messages: list[LLMMessage]) -> list[dict]:
        return [{"role": msg.role, "content": msg.content} for msg in messages]

    def _get_pricing(self, model: str) -> dict:
        return GROQ_PRICING.get(model, {"input": 0.0, "output": 0.0})

    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        pricing = self._get_pricing(self._default_model)
        return (input_tokens * pricing["input"] + output_tokens * pricing["output"]) / 1000

    async def _chat(
        self,
        messages: list[dict],
        model_name: str,
        temperature: float,
        max_tokens: int,
        json_mode: bool = False,
    ) -> tuple[dict, dict]:
        payload: dict = {
            "model": model_name,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}
        if model_name.startswith("openai/gpt-oss"):
            # Reasoning models: keep hidden chain-of-thought short so
            # completion budget is spent on actual output
            payload["reasoning_effort"] = "low"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        # Free-tier rate limits (429) are expected under parallel load -
        # retry with exponential backoff respecting Retry-After.
        max_attempts = 4
        last_error: Exception | None = None

        async with httpx.AsyncClient(timeout=120) as client:
            for attempt in range(max_attempts):
                try:
                    resp = await client.post(GROQ_API_URL, json=payload, headers=headers)
                    resp.raise_for_status()
                    data = resp.json()
                    break
                except httpx.HTTPStatusError as e:
                    last_error = e
                    status = e.response.status_code
                    if status not in (429, 500, 502, 503) or attempt == max_attempts - 1:
                        raise
                    retry_after = e.response.headers.get("retry-after")
                    delay = float(retry_after) if retry_after else min(4 ** attempt * 2, 30)
                    import asyncio as _asyncio

                    await _asyncio.sleep(delay)

        usage_data = data.get("usage", {}) or {}
        usage = {
            "input_tokens": usage_data.get("prompt_tokens", 0),
            "output_tokens": usage_data.get("completion_tokens", 0),
            "total_tokens": usage_data.get("total_tokens", 0),
        }
        content = ""
        choices = data.get("choices") or []
        if choices:
            content = (choices[0].get("message") or {}).get("content") or ""
        finish_reason = choices[0].get("finish_reason") if choices else None
        return content, {**usage, "finish_reason": finish_reason}

    async def generate(
        self,
        messages: list[LLMMessage],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs,
    ) -> LLMResponse:
        model_name = model or self._default_model

        content, usage_meta = await self._chat(
            self._convert_messages(messages),
            model_name,
            temperature,
            max_tokens,
        )

        # Reasoning models can exhaust the completion budget on hidden
        # chain-of-thought and return empty content - retry with a bigger budget
        if not content.strip() and max_tokens < 8192:
            content, usage_meta = await self._chat(
                self._convert_messages(messages),
                model_name,
                temperature,
                max(max_tokens * 4, 1024),
            )

        usage = LLMUsage(
            input_tokens=usage_meta["input_tokens"],
            output_tokens=usage_meta["output_tokens"],
            total_tokens=usage_meta["total_tokens"],
            estimated_cost=0.0,
        )
        usage.estimated_cost = self.estimate_cost(usage.input_tokens, usage.output_tokens)

        return LLMResponse(
            content=content,
            usage=usage,
            model=model_name,
            provider=self.provider_name,
            finish_reason=usage_meta.get("finish_reason"),
        )

    async def generate_structured(
        self,
        messages: list[LLMMessage],
        response_model: Type[BaseModel],
        model: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 4096,
        **kwargs,
    ) -> BaseModel:
        model_name = model or self._default_model

        schema = response_model.model_json_schema()
        schema_str = json.dumps(schema, indent=2)

        structured_prompt = (
            f"Output a valid JSON object that conforms to this schema:\n{schema_str}\n\n"
            f"Respond ONLY with the JSON object, no additional text, no markdown fences."
        )

        structured_messages = [
            *self._convert_messages(messages),
            {"role": "user", "content": structured_prompt},
        ]

        content, usage_meta = await self._chat(
            structured_messages,
            model_name,
            temperature,
            max_tokens,
            json_mode=True,
        )

        parsed_json = self._extract_json(content)

        try:
            return response_model(**parsed_json)
        except Exception as e:
            raise ValueError(f"Failed to parse structured response: {e}") from e

    @staticmethod
    def _extract_json(content: str) -> dict:
        text = (content or "").strip()

        try:
            return json.loads(text)
        except Exception:
            pass

        fence_match = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL)
        if fence_match:
            try:
                return json.loads(fence_match.group(1))
            except Exception:
                pass

        brace_match = re.search(r"\{.*\}", text, re.DOTALL)
        if brace_match:
            try:
                return json.loads(brace_match.group(0))
            except Exception:
                pass

        raise ValueError(f"No valid JSON found in response: {text[:200]}")
