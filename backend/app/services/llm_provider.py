from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Type, TypeVar, List
import logging
import time
import re
import httpx
from openai import OpenAI
from pydantic import BaseModel

from app.core.config import settings

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class LLMProvider(ABC):
    @abstractmethod
    def generate(self, prompt: str, schema: Optional[Type[T]] = None, **kwargs) -> Any:
        pass

    @abstractmethod
    def generate_structured(self, prompt: str, schema: Type[T], **kwargs) -> T:
        pass


import random

class MultiProviderLLM(LLMProvider):
    """
    Multi-Provider & Multi-Key Load Balancer & Instant Failover Manager.
    Sequence: Groq Key 1 -> Groq Key 2 -> Gemini Flash -> OpenAI gpt-4o-mini
    Implements exponential backoff with jitter for 429/rate-limit errors.
    """
    def __init__(self, max_retries_per_provider: int = 3):
        self.max_retries_per_provider = max_retries_per_provider
        self.providers: List[Dict[str, Any]] = []
        
        # 1. Groq Key 1
        if getattr(settings, "groq_api_key", None):
            self.providers.append({
                "name": "Groq-Key-1",
                "client": OpenAI(
                    api_key=settings.groq_api_key,
                    base_url="https://api.groq.com/openai/v1",
                    http_client=httpx.Client(timeout=120.0)
                ),
                "model": settings.groq_model,
                "active": True
            })
            
        # 2. Groq Key 2
        if getattr(settings, "groq_api_key_2", None):
            self.providers.append({
                "name": "Groq-Key-2",
                "client": OpenAI(
                    api_key=settings.groq_api_key_2,
                    base_url="https://api.groq.com/openai/v1",
                    http_client=httpx.Client(timeout=120.0)
                ),
                "model": settings.groq_model,
                "active": True
            })

        # 3. Gemini Key (Gemini 3.6 Flash via Google OpenAI-compatible API)
        if getattr(settings, "gemini_api_key", None):
            self.providers.append({
                "name": "Gemini-3.6-Flash",
                "client": OpenAI(
                    api_key=settings.gemini_api_key,
                    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
                    http_client=httpx.Client(timeout=120.0)
                ),
                "model": getattr(settings, "gemini_model", "gemini-3.6-flash"),
                "active": True
            })

        # 4. OpenAI Key
        if getattr(settings, "openai_api_key", None):
            self.providers.append({
                "name": "OpenAI-gpt-4o-mini",
                "client": OpenAI(
                    api_key=settings.openai_api_key,
                    http_client=httpx.Client(timeout=120.0)
                ),
                "model": getattr(settings, "openai_model", "gpt-4o-mini"),
                "active": True
            })

        self.current_idx = 0
        active_names = [p["name"] for p in self.providers if p["active"]]
        logger.info(f"[LLM POOL INIT] Initialized MultiProviderLLM pool with {len(active_names)} active providers: {active_names}")

    def _calculate_backoff(self, attempt: int, initial_delay: float = 1.0, max_delay: float = 10.0) -> float:
        """Calculate exponential backoff with randomized jitter."""
        exponential = initial_delay * (2 ** (attempt - 1))
        jitter = random.uniform(0.1, 0.5)
        return min(max_delay, exponential + jitter)

    def _make_request(self, messages: list, schema: Optional[Type[T]] = None, **kwargs) -> Any:
        active_providers = [p for p in self.providers if p["active"]]
        if not active_providers:
            # Fallback: re-enable providers if temporarily marked inactive
            for p in self.providers:
                if "insufficient_quota" not in p.get("disabled_reason", ""):
                    p["active"] = True
            active_providers = [p for p in self.providers if p["active"]]

        if not active_providers:
            raise ValueError("No active LLM providers or API keys available.")

        num_providers = len(active_providers)
        last_exception = None

        # Iterate through providers starting from current round-robin index
        for i in range(num_providers):
            idx = (self.current_idx + i) % num_providers
            provider = active_providers[idx]
            p_name = provider["name"]
            client = provider["client"]
            model = provider["model"]
            next_p_name = active_providers[(idx + 1) % num_providers]["name"] if num_providers > 1 else "None"

            for attempt in range(1, self.max_retries_per_provider + 1):
                try:
                    logger.info(f"[LLM DISPATCH] Provider used: [{p_name}] | Model: {model} | Attempt: {attempt}/{self.max_retries_per_provider}")
                    
                    response = client.chat.completions.create(
                        model=model,
                        messages=messages,
                        temperature=kwargs.get("temperature", 0.7),
                        max_tokens=kwargs.get("max_tokens", 3500),
                    )

                    content = response.choices[0].message.content or ""
                    if schema:
                        clean_content = content.strip()
                        clean_content = re.sub(r'<think>.*?</think>', '', clean_content, flags=re.DOTALL).strip()
                        if clean_content.startswith("```"):
                            lines = clean_content.splitlines()
                            if lines[0].startswith("```"):
                                lines = lines[1:]
                            if lines and lines[-1].strip() == "```":
                                lines = lines[:-1]
                            clean_content = "\n".join(lines).strip()
                        result = schema.model_validate_json(clean_content)
                        
                        # Advance round-robin index on success
                        self.current_idx = (idx + 1) % num_providers
                        logger.info(f"[LLM SUCCESS] Provider used: [{p_name}] successfully returned structured response.")
                        return result
                    else:
                        self.current_idx = (idx + 1) % num_providers
                        logger.info(f"[LLM SUCCESS] Provider used: [{p_name}] successfully returned text response.")
                        return content

                except Exception as e:
                    last_exception = e
                    err_msg = str(e).lower()

                    if "insufficient_quota" in err_msg or "credit_balance_exhausted" in err_msg:
                        logger.warning(f"[QUOTA EXHAUSTED] Provider [{p_name}] quota exhausted. Disabling this provider.")
                        provider["active"] = False
                        provider["disabled_reason"] = "insufficient_quota"
                        break  # Break retry loop for this provider, fall back to next provider

                    elif any(x in err_msg for x in ["rate", "429", "413", "overloaded", "capacity", "too many requests"]):
                        backoff = self._calculate_backoff(attempt)
                        logger.warning(
                            f"[429 OCCURRENCE] Provider [{p_name}] hit rate limit 429/TPM bound. "
                            f"Retry attempt {attempt}/{self.max_retries_per_provider}. Backing off for {backoff:.2f}s (exponential backoff + jitter)..."
                        )
                        if attempt < self.max_retries_per_provider:
                            time.sleep(backoff)
                            continue
                        else:
                            logger.warning(
                                f"[FALLBACK PROVIDER] Provider [{p_name}] exhausted {self.max_retries_per_provider} retries on 429 errors. "
                                f"Failing over to fallback provider: [{next_p_name}]"
                            )
                            break

                    elif schema and ("validation" in err_msg or "json" in err_msg or "pydantic" in err_msg):
                        logger.warning(f"[SCHEMA ERROR] Provider [{p_name}] response failed schema validation: {e}. Retry attempt {attempt}/{self.max_retries_per_provider}...")
                        if attempt < self.max_retries_per_provider:
                            time.sleep(1.0)
                            continue
                        else:
                            logger.warning(f"[FALLBACK PROVIDER] Provider [{p_name}] failed schema validation after retries. Falling back to [{next_p_name}]...")
                            break

                    else:
                        logger.warning(f"[LLM ERROR] Provider [{p_name}] error: {e}. Retry attempt {attempt}/{self.max_retries_per_provider}...")
                        if attempt < self.max_retries_per_provider:
                            time.sleep(1.0)
                            continue
                        else:
                            logger.warning(f"[FALLBACK PROVIDER] Provider [{p_name}] failed after retries. Falling back to [{next_p_name}]...")
                            break

        raise Exception(f"All configured LLM providers failed. Last error: {last_exception}")

    def generate(self, prompt: str, schema: Optional[Type[T]] = None, **kwargs) -> Any:
        sys_prompt = kwargs.get("system_prompt", "You are an expert marketing strategist.")
        if schema:
            field_names = list(schema.model_fields.keys())
            sys_prompt += f" Respond strictly with a valid JSON object matching the required schema with keys: {field_names}. Do NOT output any thinking, reasoning, or markdown text outside the JSON object. Start your response directly with '{{'."
        messages = [
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": prompt},
        ]
        return self._make_request(messages, schema, **kwargs)

    def generate_structured(self, prompt: str, schema: Type[T], **kwargs) -> T:
        return self.generate(prompt, schema=schema, **kwargs)


class MockLLMProvider(LLMProvider):
    def generate(self, prompt: str, schema: Optional[Type[T]] = None, **kwargs) -> Any:
        if schema:
            return schema.model_construct()
        return "Mock response"

    def generate_structured(self, prompt: str, schema: Type[T], **kwargs) -> T:
        return schema.model_construct()


def get_llm_provider() -> LLMProvider:
    provider = MultiProviderLLM()
    if any(p["active"] for p in provider.providers):
        return provider
    logger.warning("No active LLM API keys configured, using mock provider")
    return MockLLMProvider()

def get_visual_llm_provider() -> LLMProvider:
    if getattr(settings, "gemini_visual_api_key", None):
        provider = MultiProviderLLM()
        # Override providers to ONLY use the visual Gemini key
        provider.providers = [{
            "name": "Gemini-Visual-Dedicated",
            "client": OpenAI(
                api_key=settings.gemini_visual_api_key,
                base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
                http_client=httpx.Client(timeout=120.0)
            ),
            "model": getattr(settings, "gemini_model", "gemini-3.6-flash"),
            "active": True
        }]
        return provider
    # Fallback to standard provider pool if not configured
    return get_llm_provider()