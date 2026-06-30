"""Unified LLM client abstraction.

Supported providers (scaffold):

- ``echo``: deterministic offline stub that echoes a context excerpt.
  Keeps the whole pipeline runnable without an API key (tests & CI).
- ``gemini``: Google Gemini free-tier API (default, via ``google-genai``).
  Chosen over Groq because the free quota is larger, the models are
  multimodal-native (PDFs / tables / images), and the brief names Gemini free
  as one of the recommended options.
- ``huggingface``: HuggingFace Inference API fallback.

All providers return a uniform ``LLMResponse``. A disk cache is applied
transparently via ``PromptCache`` so re-running evals does not burn quota.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

try:
    import requests
except ImportError:  # pragma: no cover - optional for non-HTTP tests/providers
    requests = None

from rag.generation.abstention import REFUSAL_PHRASE

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - optional in minimal test environments
    def load_dotenv(*_args, **_kwargs) -> bool:
        return False

load_dotenv()

@dataclass
class LLMResponse:
    text: str
    input_tokens: int = 0
    output_tokens: int = 0
    provider: str = ""
    model: str = ""
    cached: bool = False
    finish_reason: str = ""


class LLMClient:
    """defines base architecture and shared caching logic"""
    provider: str = "base"
    model: str = ""

    def __init__(self, cache: Any | None = None) -> None:
        self.cache = cache

    def complete(
        self,
        system: str,
        user: str,
        *,
        temperature: float = 0.1,
        max_tokens: int = 512,
    ) -> LLMResponse:
        cache_key = f"{self.provider}:{self.model}:{system}:{user}:{temperature}:{max_tokens}"

        if self.cache is not None:
            cached_val = self.cache.get(cache_key)
            if cached_val is not None:
                if isinstance(cached_val, LLMResponse):
                    cached_val.cached = True
                    return cached_val
                elif isinstance(cached_val, dict):
                    cached_val["cached"] = True
                    return LLMResponse(**cached_val)

        response = self._call(system, user, temperature=temperature, max_tokens=max_tokens)

        if self.cache is not None:
            self.cache.set(cache_key, response)

        return response

    def _call(
        self, system: str, user: str, *, temperature: float, max_tokens: int
    ) -> LLMResponse:
        raise NotImplementedError


class EchoLLMClient(LLMClient):
    """keeps the whole pipeline runnable without an API key fortests & CI."""
    provider = "echo"
    model = "echo-1"

    def _call(
        self, system: str, user: str, *, temperature: float, max_tokens: int
    ) -> LLMResponse:
        citation_match = re.search(r"(\[[A-Za-z0-9_\-]+:p\d+\])", user)
        citation = citation_match.group(1) if citation_match else "[doc_unknown:p0]"

        mock_text = f"Based on the provided documents, this is a simulated response. {citation}"

        est_input = int((len(system) + len(user)) / 4)
        est_output = int(len(mock_text) / 4)

        return LLMResponse(
            text=mock_text,
            input_tokens=est_input,
            output_tokens=est_output,
            provider=self.provider,
            model=self.model,
            cached=False
        )


class GeminiLLMClient(LLMClient):
    """Google Gemini free-tier API"""
    provider = "gemini"

    def __init__(
        self, model: str | None = None, api_key: str | None = None, cache: Any | None = None
    ) -> None:
        super().__init__(cache)
        self.model = (model or os.getenv("GEMINI_MODEL") or "gemini-2.5-flash").strip()
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")

    def _call(
        self, system: str, user: str, *, temperature: float, max_tokens: int
    ) -> LLMResponse:
        if not self.api_key:
            return LLMResponse(
                text="[Gemini Error] API Key missing.",
                provider=self.provider,
                model=self.model
            )

        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=self.api_key)
            config_kwargs: dict[str, Any] = {
                "system_instruction": system,
                "temperature": temperature,
                "max_output_tokens": max_tokens,
            }
            if self.model.startswith("gemini-2.5-flash"):
                config_kwargs["thinking_config"] = types.ThinkingConfig(thinking_budget=0)
            config = types.GenerateContentConfig(**config_kwargs)

            response = client.models.generate_content(
                model=self.model,
                contents=user,
                config=config,
            )

            input_tokens = 0
            output_tokens = 0
            if response.usage_metadata:
                input_tokens = response.usage_metadata.prompt_token_count or 0
                output_tokens = response.usage_metadata.candidates_token_count or 0

            finish_reason = ""
            if response.candidates:
                finish_reason = str(response.candidates[0].finish_reason or "")

            return LLMResponse(
                text=response.text if response.text else REFUSAL_PHRASE,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                provider=self.provider,
                model=self.model,
                cached=False,
                finish_reason=finish_reason,
            )
        except Exception as e:
            return LLMResponse(
                text=f"[Gemini Error] API call failed: {str(e)}",
                provider=self.provider,
                model=self.model
            )


class OllamaLLMClient(LLMClient):
    """locally hosted model running via Ollama"""
    provider = "ollama"

    def __init__(self, model: str | None = None, cache: Any | None = None) -> None:
        super().__init__(cache)
        self.model = model.strip() if model else "llama3.1:8b"

        raw_host = os.getenv("OLLAMA_HOST", "localhost:11434").strip()

        if not raw_host.startswith("http://") and not raw_host.startswith("https://"):
            parsed_host = urlparse(f"http://{raw_host}")
        else:
            parsed_host = urlparse(raw_host)

        netloc = f"{parsed_host.netloc}:11434" if parsed_host.port is None else parsed_host.netloc

        base_url = f"{parsed_host.scheme}://{netloc}"
        self.api_url = f"{base_url}/api/chat"
        print(f"\n[Ollama Client] Context established target route: {self.api_url}")

    def _call(
        self, system: str, user: str, *, temperature: float, max_tokens: int
    ) -> LLMResponse:
        if requests is None:
            return LLMResponse(
                text="[Ollama Error] requests dependency missing.",
                provider=self.provider,
                model=self.model,
            )

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user}
            ],
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            },
            "stream": False
        }

        try:
            response = requests.post(self.api_url, json=payload, timeout=30)
            response.raise_for_status()
            res_json = response.json()

            output_text = res_json.get("message", {}).get("content", "")
            return LLMResponse(
                text=output_text if output_text else REFUSAL_PHRASE,
                input_tokens=res_json.get("prompt_eval_count", 0),
                output_tokens=res_json.get("eval_count", 0),
                provider=self.provider,
                model=self.model,
                cached=False
            )
        except Exception as e:
            return LLMResponse(
                text=f"[Ollama Error] Connection failed: {str(e)}",
                provider=self.provider,
                model=self.model
            )


class HuggingFaceLLMClient(LLMClient):
    """HuggingFace Inference API fallback."""
    provider = "huggingface"

    def __init__(
        self, model: str | None = None, api_token: str | None = None, cache: Any | None = None
    ) -> None:
        super().__init__(cache)
        self.model = (model or os.getenv("HF_MODEL") or "Qwen/Qwen2.5-7B-Instruct").strip()
        self.api_token = api_token or os.getenv("HF_API_TOKEN")
        self.api_url = "https://router.huggingface.co/v1/chat/completions"

    def _call(
        self, system: str, user: str, *, temperature: float, max_tokens: int
    ) -> LLMResponse:
        if not self.api_token:
            return LLMResponse(
                text="[HuggingFace Error] API Token missing.",
                provider=self.provider,
                model=self.model
            )
        if requests is None:
            return LLMResponse(
                text="[HuggingFace Error] requests dependency missing.",
                provider=self.provider,
                model=self.model,
            )

        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user}
            ],
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        try:
            response = requests.post(self.api_url, json=payload, headers=headers, timeout=30)
            if not response.ok:
                detail = response.text.strip()
                raise RuntimeError(
                    f"{response.status_code} {response.reason}: {detail[:1000]}"
                )
            res_json = response.json()

            output_text = ""
            if "choices" in res_json and len(res_json["choices"]) > 0:
                output_text = res_json["choices"][0].get("message", {}).get("content", "")

            usage = res_json.get("usage", {})

            input_tokens = usage.get("prompt_tokens", int((len(system) + len(user)) / 4))
            output_tokens = usage.get("completion_tokens", int(len(output_text) / 4))

            return LLMResponse(
                text=output_text.strip() if output_text else REFUSAL_PHRASE,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                provider=self.provider,
                model=self.model,
                cached=False
            )
        except Exception as e:
            return LLMResponse(
                text=f"[HuggingFace Error] Router call failed: {str(e)}",
                provider=self.provider,
                model=self.model
            )


def build_llm_client(
    provider: str, model: str | None = None, cache_dir: str | None = None
) -> LLMClient:
    cache = None
    if cache_dir:
        try:
            from rag.cache import PromptCache
            cache = PromptCache(cache_dir)
        except ImportError:
            cache = None

    prov_lower = provider.lower()
    if prov_lower == "ollama":
        return OllamaLLMClient(model=model, cache=cache)
    elif prov_lower == "gemini":
        return GeminiLLMClient(model=model, cache=cache)
    elif prov_lower == "huggingface":
        return HuggingFaceLLMClient(model=model, cache=cache)
    else:
        return EchoLLMClient(cache)
