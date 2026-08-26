import json
import logging
from abc import ABC, abstractmethod
from typing import Optional, Type, TypeVar
from pydantic import BaseModel

from src.config import Config

logger = logging.getLogger(__name__)
T = TypeVar("T", bound=BaseModel)


class LLMClient(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    def generate_text(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.4,
    ) -> str:
        """Generate plain text from prompt."""
        pass

    @abstractmethod
    def generate_structured(
        self,
        prompt: str,
        response_schema: Type[T],
        system_instruction: Optional[str] = None,
        temperature: float = 0.0,
    ) -> T:
        """Generate structured data conforming to a Pydantic schema."""
        pass


class GeminiClient(LLMClient):
    """Google Gemini client using official google-genai SDK."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or Config.GEMINI_API_KEY
        if not self.api_key:
            raise ValueError(
                "Gemini API key is required. Set GEMINI_API_KEY or GOOGLE_API_KEY in .env"
            )
        self.model = model or Config.GEMINI_MODEL
        self.fallback_models = [
            self.model,
            "gemini-2.5-flash-lite",
            "gemini-3.5-flash-lite",
            "gemini-3.5-flash",
            "gemini-3.6-flash",
        ]
        from google import genai
        self.client = genai.Client(api_key=self.api_key)

    def _execute_with_fallback(self, func, *args, **kwargs):
        """Execute a Gemini API call with model fallback and rate-limit backoff."""
        import time
        import re

        last_error = None
        for model in self.fallback_models:
            for attempt in range(3):
                try:
                    return func(model, *args, **kwargs)
                except Exception as e:
                    last_error = e
                    err_str = str(e)
                    
                    # Check for rate limit / quota exhaustion
                    if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                        # Extract suggested retry delay if provided
                        delay = 12.0
                        match = re.search(r"retry in (\d+\.?\d*)s", err_str)
                        if match:
                            delay = float(match.group(1)) + 1.0
                        
                        logger.warning(
                            f"Rate limit on model '{model}'. Sleeping {delay:.1f}s before retry (Attempt {attempt+1}/3)..."
                        )
                        time.sleep(delay)
                        continue
                    elif "404" in err_str or "NOT_FOUND" in err_str:
                        logger.warning(f"Model '{model}' not available (404). Falling back to next model...")
                        break
                    else:
                        raise e

        raise last_error

    def generate_text(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.4,
    ) -> str:
        from google.genai import types

        def _call(model):
            config = types.GenerateContentConfig(
                temperature=temperature,
                system_instruction=system_instruction if system_instruction else None,
            )
            response = self.client.models.generate_content(
                model=model,
                contents=prompt,
                config=config,
            )
            return response.text or ""

        return self._execute_with_fallback(_call)

    def generate_structured(
        self,
        prompt: str,
        response_schema: Type[T],
        system_instruction: Optional[str] = None,
        temperature: float = 0.0,
    ) -> T:
        from google.genai import types

        def _call(model):
            config = types.GenerateContentConfig(
                temperature=temperature,
                system_instruction=system_instruction if system_instruction else None,
                response_mime_type="application/json",
                response_schema=response_schema,
            )
            response = self.client.models.generate_content(
                model=model,
                contents=prompt,
                config=config,
            )

            if hasattr(response, "parsed") and response.parsed is not None:
                if isinstance(response.parsed, response_schema):
                    return response.parsed
                elif isinstance(response.parsed, dict):
                    return response_schema.model_validate(response.parsed)

            # Fallback: Parse text JSON
            text = response.text or "{}"
            clean_text = text.strip()
            if clean_text.startswith("```json"):
                clean_text = clean_text[7:]
            if clean_text.startswith("```"):
                clean_text = clean_text[3:]
            if clean_text.endswith("```"):
                clean_text = clean_text[:-3]
            clean_text = clean_text.strip()

            data = json.loads(clean_text)
            return response_schema.model_validate(data)

        return self._execute_with_fallback(_call)


class OpenAIClient(LLMClient):
    """OpenAI client using official openai SDK."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or Config.OPENAI_API_KEY
        if not self.api_key:
            raise ValueError(
                "OpenAI API key is required. Set OPENAI_API_KEY in .env"
            )
        self.model = model or Config.OPENAI_MODEL
        import openai
        self.client = openai.OpenAI(api_key=self.api_key)

    def generate_text(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.4,
    ) -> str:
        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
        )
        return response.choices[0].message.content or ""

    def generate_structured(
        self,
        prompt: str,
        response_schema: Type[T],
        system_instruction: Optional[str] = None,
        temperature: float = 0.0,
    ) -> T:
        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})

        completion = self.client.beta.chat.completions.parse(
            model=self.model,
            messages=messages,
            response_format=response_schema,
            temperature=temperature,
        )
        return completion.choices[0].message.parsed


class MockLLMClient(LLMClient):
    """Mock client for offline deterministic testing."""

    def __init__(self, default_response: str = "Mocked lesson content", default_verdict: bool = True):
        self.default_response = default_response
        self.default_verdict = default_verdict
        self.calls = []

    def generate_text(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.4,
    ) -> str:
        self.calls.append({"type": "text", "prompt": prompt, "system": system_instruction})
        return self.default_response

    def generate_structured(
        self,
        prompt: str,
        response_schema: Type[T],
        system_instruction: Optional[str] = None,
        temperature: float = 0.0,
    ) -> T:
        self.calls.append({"type": "structured", "prompt": prompt, "schema": response_schema.__name__})
        if response_schema.__name__ == "CheckpointEvaluation":
            # Extract checkpoint name if possible
            cp_name = "Mock Checkpoint"
            for line in prompt.split("\n"):
                if "RUBRIC CHECKPOINT:" in line:
                    cp_name = line.split(":", 1)[1].strip()
                    break
            return response_schema(
                checkpoint_name=cp_name,
                passed=self.default_verdict,
                reasoning="Mock evaluation reasoning.",
                suggestion="" if self.default_verdict else "Mock suggestion to fix failure."
            )
        return response_schema.model_validate({"passed": self.default_verdict})


def get_llm_client(
    provider: Optional[str] = None,
    model: Optional[str] = None,
    api_key: Optional[str] = None,
    mock: bool = False,
) -> LLMClient:
    """Factory to get the appropriate LLM client instance."""
    if mock:
        return MockLLMClient()

    prov = (provider or Config.DEFAULT_PROVIDER).lower()
    if prov in ["gemini", "google"]:
        return GeminiClient(api_key=api_key, model=model)
    elif prov == "openai":
        return OpenAIClient(api_key=api_key, model=model)
    elif prov == "mock":
        return MockLLMClient()
    else:
        raise ValueError(f"Unsupported LLM provider: {prov}. Choose 'gemini' or 'openai'.")
