"""Optional cross-encoder reranker (M4).

TODO:
- Lazy-load sentence_transformers.CrossEncoder on first call.
- Score (query, chunk.text) pairs, return top_n reordered RetrievalResults.
- Pass-through if the model cannot be loaded.
"""

from __future__ import annotations

from rag.types import RetrievalResult


class CrossEncoderReranker:
    def __init__(self, model_name: str = "BAAI/bge-reranker-base") -> None:
        self.model_name = model_name

    def rerank(
        self, query: str, hits: list[RetrievalResult], top_n: int
    ) -> list[RetrievalResult]:
        raise NotImplementedError
