"""Build a retriever from ``RetrievalConfig``.

TODO (M2): dispatch on ``cfg.mode`` to DenseRetriever / BM25Retriever /
HybridRetriever and return the configured instance.
"""

from __future__ import annotations

from rag.config import RetrievalConfig
from rag.retrieval.base import Retriever
from rag.retrieval.bm25 import BM25Retriever
from rag.retrieval.dense import DenseRetriever
from rag.retrieval.hybrid import HybridRetriever


def build_retriever(cfg: RetrievalConfig) -> Retriever:
    
    mode = cfg.mode.lower()

    if mode == "bm25":
        return BM25Retriever()

    if mode == "dense":
        return DenseRetriever(
            embedding_model=cfg.embedding_model,
            store=cfg.store,
            store_dir=cfg.store_dir,
        )

    if mode == "hybrid":
        dense = DenseRetriever(
            embedding_model=cfg.embedding_model,
            store=cfg.store,
            store_dir=cfg.store_dir,
        )

        sparse = BM25Retriever()

        return HybridRetriever(
            dense=dense,
            sparse=sparse,
        )

    raise ValueError(f"Unknown retrieval mode: {cfg.mode}")
