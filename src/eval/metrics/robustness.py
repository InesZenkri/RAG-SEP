"""Category 5 - Robustness.

Slice the per-item results by metadata (long_doc, tabular, multi_column,
scanned, contradiction) and report per-slice answer F1 / grounding / abstention.
Useful for the final report's "where does the system break?" table.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from eval.dataset import EvalItem
from eval.metrics.abstention import false_answer_rate, false_refusal_rate
from eval.metrics.answer import token_f1
from eval.metrics.grounding import citation_precision, citation_recall
from rag.types import Answer


_DEFAULT_SLICE_KEYS = (
    "long_doc",
    "tabular",
    "multi_column",
    "scanned",
    "contradiction",
)


def _metadata_values(item: EvalItem, key: str) -> list[Any]:
    value = item.metadata.get(key)
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        return list(value)
    return [value]


def _slice_name(key: str, value: Any) -> str:
    if isinstance(value, bool):
        return key if value else f"not_{key}"
    return f"{key}:{value}"


def slice_by(
    pairs: list[tuple[EvalItem, Answer]], key: str
) -> dict[str, list[tuple[EvalItem, Answer]]]:
    """Group eval pairs by an EvalItem field or metadata value.

    Examples:
    - ``slice_by(pairs, "type")`` groups by ``item.type``.
    - ``slice_by(pairs, "contradiction")`` groups items whose metadata has
      ``{"contradiction": true}`` into the ``contradiction`` slice.
    - list metadata values create one slice per value.
    """
    slices: dict[str, list[tuple[EvalItem, Answer]]] = defaultdict(list)

    for item, answer in pairs:
        if hasattr(item, key):
            values = [getattr(item, key)]
        else:
            values = _metadata_values(item, key)

        for value in values:
            if value is None or value is False:
                continue
            slices[_slice_name(key, value)].append((item, answer))

    return dict(slices)


def _is_answerable(item: EvalItem) -> bool:
    return bool(item.answer or item.expected_answers)


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _slice_metrics(pairs: list[tuple[EvalItem, Answer]]) -> dict[str, float]:
    answerable_f1: list[float] = []
    citation_precisions: list[float] = []
    citation_recalls: list[float] = []
    confidences: list[float] = []
    abstentions = 0

    for item, answer in pairs:
        if _is_answerable(item):
            refs = item.expected_answers or ([item.answer] if item.answer else [])
            answerable_f1.append(token_f1(answer.text, refs))

        citation_precisions.append(citation_precision(answer))
        citation_recalls.append(citation_recall(answer))
        confidences.append(answer.confidence)
        if answer.abstained:
            abstentions += 1

    count = len(pairs)
    return {
        "count": float(count),
        "answer_token_f1": _mean(answerable_f1),
        "citation_precision": _mean(citation_precisions),
        "citation_recall": _mean(citation_recalls),
        "false_refusal_rate": false_refusal_rate(pairs),
        "false_answer_rate": false_answer_rate(pairs),
        "abstention_rate": abstentions / count if count else 0.0,
        "avg_confidence": _mean(confidences),
    }


def robustness_report(
    pairs: list[tuple[EvalItem, Answer]],
) -> dict[str, dict[str, float]]:
    """Return ``{slice_name: {metric_name: value}}``."""
    report: dict[str, dict[str, float]] = {}
    if not pairs:
        return report

    report["all"] = _slice_metrics(pairs)

    for key in ("type", *_DEFAULT_SLICE_KEYS):
        for name, slice_pairs in slice_by(pairs, key).items():
            if slice_pairs:
                report[name] = _slice_metrics(slice_pairs)

    return report
