"""Evaluation dataset loaders.

An ``EvalItem`` captures everything a metric needs: the question, a gold
answer (or ``None`` for unanswerable items), the gold documents/pages, and a
``type`` tag used to slice metrics by (extractive / abstractive /
unanswerable / contradiction / robustness_*).

TODO (M1):
- load_jsonl(path): yield EvalItem from a JSONL file.
- load_suite(name): return (corpus_paths, items) for suites "smoke", "full",
  "adversarial", "robustness".
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable


@dataclass
class EvalItem:
    id: str
    question: str
    answer: str | None = None
    expected_answers: list[str] = field(default_factory=list)
    doc_ids: list[str] = field(default_factory=list)
    doc_sources: list[str] = field(default_factory=list)
    pages: list[int] = field(default_factory=list)
    type: str = "extractive"
    metadata: dict = field(default_factory=dict)


def load_jsonl(path: str | Path) -> list[EvalItem]:
    raise NotImplementedError


def load_suite(name: str) -> tuple[list[Path], list[EvalItem]]:
    """Return ``(corpus_paths, eval_items)`` for a named suite."""
    raise NotImplementedError
