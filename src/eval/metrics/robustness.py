"""Category 5 - Robustness.

Slice the per-item results by metadata (long_doc, tabular, multi_column,
scanned, contradiction) and report per-slice answer F1 / grounding / abstention.
Useful for the final report's "where does the system break?" table.
"""

from __future__ import annotations

from eval.dataset import EvalItem
from rag.types import Answer


def slice_by(
    pairs: list[tuple[EvalItem, Answer]], key: str
) -> dict[str, list[tuple[EvalItem, Answer]]]:
    raise NotImplementedError


def robustness_report(
    pairs: list[tuple[EvalItem, Answer]],
) -> dict[str, dict[str, float]]:
    """Return ``{slice_name: {metric_name: value}}``."""
    raise NotImplementedError
