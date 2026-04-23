"""Shared pytest fixtures.

Provides tiny in-memory Document / Chunk objects so tests do not need the PDF
parsing stack, and a shared path to the sample corpus.
"""

from __future__ import annotations

from pathlib import Path

import pytest

SAMPLE_DIR = Path(__file__).resolve().parents[1] / "datasets" / "sample"


@pytest.fixture
def sample_dir() -> Path:
    return SAMPLE_DIR


@pytest.fixture
def sample_corpus_paths() -> list[Path]:
    return sorted((SAMPLE_DIR / "corpus").glob("*.txt"))


@pytest.fixture
def sample_qa_path() -> Path:
    return SAMPLE_DIR / "qa.jsonl"
