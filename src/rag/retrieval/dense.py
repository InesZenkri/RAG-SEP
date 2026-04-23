"""Dense retriever: in-memory cosine similarity, optional Chroma persistence.

TODO (M2):
- index(chunks): embed texts, store matrix or push to Chroma collection.
- query(text, top_k): embed query, return top-k RetrievalResult objects.
"""

from __future__ import annotations

from rag.retrieval.base import Retriever
from rag.retrieval.embeddings import Embedder
from rag.types import Chunk, RetrievalResult


class DenseRetriever(Retriever):
    name = "dense"

    def __init__(
        self,
        embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2",
        store: str = "memory",
        store_dir: str | None = None,
        embedder: Embedder | None = None,
    ) -> None:
        self.embedding_model = embedding_model
        self.store = store
        self.store_dir = store_dir
        self.embedder = embedder

    def index(self, chunks: list[Chunk]) -> None:
        raise NotImplementedError

    def query(self, text: str, top_k: int) -> list[RetrievalResult]:
        raise NotImplementedError
