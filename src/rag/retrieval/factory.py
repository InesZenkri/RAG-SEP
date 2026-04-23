"""Build a retriever from ``RetrievalConfig``.

TODO (M2): dispatch on ``cfg.mode`` to DenseRetriever / BM25Retriever /
HybridRetriever and return the configured instance.
"""

from __future__ import annotations

from rag.config import RetrievalConfig
from rag.retrieval.base import Retriever


def build_retriever(cfg: RetrievalConfig) -> Retriever:
    raise NotImplementedError
