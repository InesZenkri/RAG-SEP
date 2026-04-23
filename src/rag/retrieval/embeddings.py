"""Embedding provider.

TODO (M2 -> M4):
- SentenceTransformerEmbedder: wrap sentence-transformers (default baseline).
- GeminiEmbedder: wrap google-genai ``embed_content`` for ``text-embedding-004``.
- HashedEmbedder: deterministic offline fallback so tests run without ML deps.
- build_embedder(model_name): dispatch based on prefix (e.g. ``gemini/``).
"""

from __future__ import annotations

from typing import Protocol

import numpy as np


class Embedder(Protocol):
    dim: int

    def embed(self, texts: list[str]) -> np.ndarray: ...


class HashedEmbedder:
    def __init__(self, dim: int = 384) -> None:
        self.dim = dim

    def embed(self, texts: list[str]) -> np.ndarray:
        raise NotImplementedError


class SentenceTransformerEmbedder:
    def __init__(self, model_name: str) -> None:
        raise NotImplementedError

    def embed(self, texts: list[str]) -> np.ndarray:
        raise NotImplementedError


class GeminiEmbedder:
    def __init__(self, model_name: str = "text-embedding-004") -> None:
        raise NotImplementedError

    def embed(self, texts: list[str]) -> np.ndarray:
        raise NotImplementedError


def build_embedder(model_name: str) -> Embedder:
    raise NotImplementedError
