"""Retrieval: dense, BM25, hybrid, optional reranking."""

from rag.retrieval.base import Retriever
from rag.retrieval.bm25 import BM25Retriever
from rag.retrieval.factory import build_retriever


def __getattr__(name: str):
    if name == "DenseRetriever":
        from rag.retrieval.dense import DenseRetriever

        return DenseRetriever
    if name == "HybridRetriever":
        from rag.retrieval.hybrid import HybridRetriever

        return HybridRetriever
    raise AttributeError(name)

__all__ = [
    "Retriever",
    "BM25Retriever",
    "DenseRetriever",
    "HybridRetriever",
    "build_retriever",
]
