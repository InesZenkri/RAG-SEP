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

from dataclasses import dataclass

from rag.cache import PromptCache


@dataclass
class LLMResponse:
    text: str
    input_tokens: int = 0
    output_tokens: int = 0
    provider: str = ""
    model: str = ""
    cached: bool = False


class LLMClient:
    provider: str = "base"
    model: str = ""

    def __init__(self, cache: PromptCache | None = None) -> None:
        self.cache = cache

    def complete(
        self,
        system: str,
        user: str,
        *,
        temperature: float = 0.1,
        max_tokens: int = 512,
    ) -> LLMResponse:
        """Cache-aware wrapper around ``_call``."""
        raise NotImplementedError

    def _call(
        self, system: str, user: str, *, temperature: float, max_tokens: int
    ) -> LLMResponse:
        raise NotImplementedError


class EchoLLMClient(LLMClient):
    """Deterministic offline stub. Returns an excerpt of the retrieved context
    and copies the first citation marker it sees, so downstream code paths
    (citation extraction, validation, confidence) are exercised in tests."""

    provider = "echo"
    model = "echo-1"

    def _call(
        self, system: str, user: str, *, temperature: float, max_tokens: int
    ) -> LLMResponse:
        raise NotImplementedError


class GeminiLLMClient(LLMClient):
    """google-genai backed client for Gemini models (free tier by default).

    TODO (M2):
    - Read GEMINI_API_KEY from env.
    - Use ``google.genai.Client.models.generate_content`` with a combined
      system+user prompt, temperature, and max_output_tokens.
    - Surface usage metadata into input/output_tokens when available.
    """

    provider = "gemini"

    def __init__(
        self, model: str, api_key: str, cache: PromptCache | None = None
    ) -> None:
        super().__init__(cache)
        self.model = model
        self.api_key = api_key

    def _call(
        self, system: str, user: str, *, temperature: float, max_tokens: int
    ) -> LLMResponse:
        raise NotImplementedError


class HuggingFaceLLMClient(LLMClient):
    provider = "huggingface"

    def __init__(
        self, model: str, api_token: str, cache: PromptCache | None = None
    ) -> None:
        super().__init__(cache)
        self.model = model
        self.api_token = api_token

    def _call(
        self, system: str, user: str, *, temperature: float, max_tokens: int
    ) -> LLMResponse:
        raise NotImplementedError


def build_llm_client(
    provider: str, model: str, cache_dir: str | None = None
) -> LLMClient:
    """Dispatch by provider, falling back to EchoLLMClient when credentials
    are missing so the pipeline always has *some* generator available."""
    raise NotImplementedError
