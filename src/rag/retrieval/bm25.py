"""BM25 lexical retriever.

TODO (M4):
- Tokenise each chunk and fit a BM25Okapi index (rank_bm25 when available).
- Return top-k RetrievalResults with raw BM25 scores.
- Include a minimal pure-Python BM25 fallback so CI runs without rank_bm25.
"""

from __future__ import annotations

from rag.retrieval.base import Retriever
from rag.types import Chunk, RetrievalResult


class BM25Retriever(Retriever):
    name = "bm25"

    def __init__(self, k1: float = 1.5, b: float = 0.75) -> None:
        self.k1 = k1
        self.b = b

    def index(self, chunks: list[Chunk]) -> None:
        raise NotImplementedError

    def query(self, text: str, top_k: int) -> list[RetrievalResult]:
        raise NotImplementedError
