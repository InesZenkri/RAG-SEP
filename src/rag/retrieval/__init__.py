"""Retrieval: dense, BM25, hybrid, optional reranking."""

from rag.retrieval.base import Retriever
from rag.retrieval.bm25 import BM25Retriever
from rag.retrieval.dense import DenseRetriever
from rag.retrieval.factory import build_retriever
from rag.retrieval.hybrid import HybridRetriever

__all__ = [
    "Retriever",
    "BM25Retriever",
    "DenseRetriever",
    "HybridRetriever",
    "build_retriever",
]
