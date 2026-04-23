"""Category 1 - Retrieval quality.

Metrics: Recall@k, nDCG@k, MRR, Hit@k.

A retrieval is "correct" when any retrieved chunk's (doc_id, page) matches any
pair in the gold set for the item.
"""

from __future__ import annotations

from rag.types import RetrievalResult


def recall_at_k(retrieved: list[RetrievalResult], gold_keys: set[str], k: int) -> float:
    raise NotImplementedError


def mrr(retrieved: list[RetrievalResult], gold_keys: set[str]) -> float:
    raise NotImplementedError


def ndcg_at_k(retrieved: list[RetrievalResult], gold_keys: set[str], k: int) -> float:
    raise NotImplementedError


def hit_at_k(retrieved: list[RetrievalResult], gold_keys: set[str], k: int) -> float:
    raise NotImplementedError
