"""Confidence scoring.

Baseline heuristic (M5): geometric mean of top-k retrieval scores, clamped to
[0, 1], plus a small bonus proportional to the fraction of citations that
passed validation.

Later (M5 extension): calibrate with isotonic regression against a held-out
set of answer-correct / answer-wrong labels.
"""

from __future__ import annotations

import math
from rag.generation.citation import CitationSupport
from rag.types import RetrievalResult


BONUS_MAX = 0.1 


def compute_confidence(
    retrieved: list[RetrievalResult],
    citation_supports: list[CitationSupport] | None = None,
    k: int = 3,
) -> float:
    """Computes a confidence score bound to [0, 1]""" 
    if not retrieved:
        return 0.0

    sorted_scores = sorted([r.score for r in retrieved], reverse=True)
    top_k_scores = sorted_scores[:k]

    clamped_scores = [max(0.0, score) for score in top_k_scores]
    geo_mean = math.prod(clamped_scores) ** (1.0 / len(clamped_scores))
    confidence_base = max(0.0, min(1.0, geo_mean))


    citation_bonus = 0.0
    if citation_supports:
       valid_count = sum(1 for c in citation_supports if c.supported)
       citation_bonus = (valid_count / len(citation_supports)) * BONUS_MAX
       
    return max(0.0, min(1.0, confidence_base + citation_bonus))