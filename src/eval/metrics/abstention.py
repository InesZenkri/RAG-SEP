"""Category 4 - Abstention behaviour.

- false_refusal_rate: fraction of answerable items the system refused.
- false_answer_rate:  fraction of unanswerable items the system answered.
- precision_coverage_curve: thresholded coverage vs. answer precision, used
  to pick the abstention threshold in the final report.
"""

from __future__ import annotations

from eval.dataset import EvalItem
from rag.types import Answer


def false_refusal_rate(pairs: list[tuple[EvalItem, Answer]]) -> float:
    raise NotImplementedError


def false_answer_rate(pairs: list[tuple[EvalItem, Answer]]) -> float:
    raise NotImplementedError


def precision_coverage_curve(
    pairs: list[tuple[EvalItem, Answer]],
) -> list[tuple[float, float, float]]:
    """Return [(threshold, coverage, precision), ...] sorted by threshold."""
    raise NotImplementedError
