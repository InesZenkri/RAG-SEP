"""Hybrid retriever combining dense and BM25.

Supports two fusion modes (M4):
- ``rrf`` (Reciprocal Rank Fusion, default): robust to score-scale differences.
- ``linear``: min-max normalised scores combined as alpha*dense + (1-alpha)*bm25.
"""

from __future__ import annotations

from rag.retrieval.base import Retriever
from rag.retrieval.bm25 import BM25Retriever
from rag.retrieval.dense import DenseRetriever
from rag.types import Chunk, RetrievalResult


class HybridRetriever(Retriever):
    name = "hybrid"

    def __init__(
        self,
        dense: DenseRetriever,
        sparse: BM25Retriever,
        mode: str = "rrf",
        alpha: float = 0.5,
        rrf_k: int = 60,
    ) -> None:
        self.dense = dense
        self.sparse = sparse
        self.mode = mode
        self.alpha = alpha
        self.rrf_k = rrf_k

    def index(self, chunks: list[Chunk]) -> None:
        raise NotImplementedError

    def query(self, text: str, top_k: int) -> list[RetrievalResult]:
        raise NotImplementedError
