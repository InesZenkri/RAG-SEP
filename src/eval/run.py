"""Eval entry point: ``python -m eval.run --suite smoke --config configs/baseline.yaml``.

Pipeline:
1. Load PipelineConfig + suite (corpus_paths, eval_items).
2. Build RAGPipeline, index the corpus.
3. For each EvalItem, call pipeline.answer(question) and collect results.
4. Compute all six categories of metrics.
5. Render report.json + report.md under reports/runs/<timestamp>/.

TODO (M1): implement; CI will call this with ``--suite smoke`` as the gate.
"""

from __future__ import annotations

import argparse


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the RAG evaluation suite.")
    parser.add_argument("--suite", default="smoke", choices=["smoke", "full", "adversarial", "robustness"])
    parser.add_argument("--config", default="configs/baseline.yaml")
    parser.add_argument("--out", default="reports/runs")
    parser.add_argument("--tag", default=None, help="Optional run label.")
    args = parser.parse_args(argv)  # noqa: F841 - used by the real implementation
    raise NotImplementedError


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
