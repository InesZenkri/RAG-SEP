"""Open RAG Benchmark adapter (Vectara).

Upstream: https://github.com/vectara/open-rag-bench
Dataset: 1000 arXiv PDFs + ~3045 QA pairs (extractive / abstractive / multimodal).

TODO (M1 download script, M8 full run):
- load_corpus(dataset_dir) -> list[Path]
- load_questions(dataset_dir) -> list[EvalItem] with type tags preserved.
- Populate EvalItem.doc_ids by mapping the benchmark's document identifiers
  to our own parser-assigned doc_ids (SHA1 prefix of resolved path).
"""

from __future__ import annotations

from pathlib import Path

from eval.dataset import EvalItem


def load_corpus(dataset_dir: str | Path) -> list[Path]:
    raise NotImplementedError


def load_questions(dataset_dir: str | Path) -> list[EvalItem]:
    raise NotImplementedError
