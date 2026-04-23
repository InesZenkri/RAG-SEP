"""Adapter for the tiny in-repo ``datasets/sample`` corpus.

Powers the smoke suite (fast, runs in CI without downloading anything).
"""

from __future__ import annotations

from pathlib import Path

from eval.dataset import EvalItem


def load_corpus(dataset_dir: str | Path = "datasets/sample/corpus") -> list[Path]:
    raise NotImplementedError


def load_questions(dataset_dir: str | Path = "datasets/sample") -> list[EvalItem]:
    raise NotImplementedError
