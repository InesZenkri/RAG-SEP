"""Confidence scoring.

Baseline heuristic (M5): geometric mean of top-k retrieval scores, clamped to
[0, 1], plus a small bonus proportional to the fraction of citations that
passed validation.

Later (M5 extension): calibrate with isotonic regression against a held-out
set of answer-correct / answer-wrong labels.
"""

from __future__ import annotations

from rag.generation.citation import CitationSupport
from rag.types import RetrievalResult


def compute_confidence(
    retrieved: list[RetrievalResult],
    citation_supports: list[CitationSupport] | None = None,
    k: int = 3,
) -> float:
    raise NotImplementedError
