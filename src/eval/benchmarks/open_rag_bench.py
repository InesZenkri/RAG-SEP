"""Adapter for the Vectara Open RAG Benchmark prepared dataset."""

from __future__ import annotations

from pathlib import Path

from eval.dataset import EvalItem, load_jsonl


def _prepared_dir(dataset_dir: str | Path) -> Path:
    return Path(dataset_dir) / "prepared"


def load_corpus(dataset_dir: str | Path) -> list[Path]:
    corpus_dir = _prepared_dir(dataset_dir) / "corpus"
    if not corpus_dir.exists():
        raise FileNotFoundError(
            f"Prepared Open RAG Benchmark corpus not found at {corpus_dir}. "
            "Run: python scripts/download_benchmark.py --subset 50"
        )
    corpus = sorted(corpus_dir.glob("*.txt"))
    if not corpus:
        raise FileNotFoundError(f"No prepared corpus files found in {corpus_dir}.")
    return corpus


def load_questions(dataset_dir: str | Path) -> list[EvalItem]:
    qa_path = _prepared_dir(dataset_dir) / "qa.jsonl"
    if not qa_path.exists():
        raise FileNotFoundError(
            f"Prepared Open RAG Benchmark QA file not found at {qa_path}. "
            "Run: python scripts/download_benchmark.py --subset 50"
        )
    return load_jsonl(qa_path)
