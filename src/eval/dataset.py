"""Evaluation dataset loaders."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

# path to datasets/ relative to this file (src/eval/dataset.py -> code/datasets/)
_DATASETS_ROOT = Path(__file__).resolve().parents[2] / "datasets"

_EVAL_ITEM_FIELDS = {
    "id", "question", "answer", "expected_answers",
    "doc_ids", "doc_sources", "pages", "type", "metadata",
}


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
    """Load a JSONL file into a list of EvalItems.

    Unknown fields (like expected_behavior in the contradictions file) go
    into metadata so the loader doesn't crash on future files.
    """
    items: list[EvalItem] = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        raw: dict = json.loads(line)
        known = {k: v for k, v in raw.items() if k in _EVAL_ITEM_FIELDS}
        extra = {k: v for k, v in raw.items() if k not in _EVAL_ITEM_FIELDS}
        if extra:
            known.setdefault("metadata", {}).update(extra)
        items.append(EvalItem(**known))
    return items


def load_suite(name: str) -> tuple[list[Path], list[EvalItem]]:
    """Return (corpus_paths, eval_items) for a named test suite.

    Suites: smoke (small, runs in CI), full (full benchmark, needs download),
    adversarial (unanswerable + contradictions), robustness (mix of all).
    """
    sample_dir = _DATASETS_ROOT / "sample"
    adversarial_dir = _DATASETS_ROOT / "adversarial"
    bench_dir = _DATASETS_ROOT / "open_rag_bench"

    if name == "smoke":
        corpus = sorted((sample_dir / "corpus").glob("*.txt"))
        items = load_jsonl(sample_dir / "qa.jsonl")

    elif name == "full":
        if not bench_dir.exists():
            raise FileNotFoundError(
                f"Open RAG Benchmark not found at {bench_dir}. "
                "Run: python scripts/download_benchmark.py --subset 50"
            )
        corpus = sorted(bench_dir.glob("*.pdf"))
        items = load_jsonl(bench_dir / "qa.jsonl")

    elif name == "adversarial":
        contradiction_dir = adversarial_dir / "contradictions"
        corpus = sorted(contradiction_dir.glob("*.txt"))
        items = (
            load_jsonl(adversarial_dir / "unanswerable.jsonl")
            + load_jsonl(adversarial_dir / "contradictions.jsonl")
        )

    elif name == "robustness":
        # mix sample + adversarial so all item types are covered
        contradiction_dir = adversarial_dir / "contradictions"
        corpus = sorted((sample_dir / "corpus").glob("*.txt")) + sorted(
            contradiction_dir.glob("*.txt")
        )
        items = (
            load_jsonl(sample_dir / "qa.jsonl")
            + load_jsonl(adversarial_dir / "unanswerable.jsonl")
            + load_jsonl(adversarial_dir / "contradictions.jsonl")
        )

    else:
        raise ValueError(
            f"Unknown suite '{name}'. "
            "Choose from: smoke, full, adversarial, robustness."
        )

    return corpus, items
