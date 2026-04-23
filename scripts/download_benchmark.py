"""Download the Vectara Open RAG Benchmark into ``datasets/open_rag_bench/``.

Usage:
    python scripts/download_benchmark.py --subset 50    # 50 PDFs for fast iteration
    python scripts/download_benchmark.py --subset all   # full 1000-PDF corpus

TODO (M1):
- Use ``huggingface_hub.snapshot_download`` to fetch the dataset.
- Write a manifest mapping the benchmark's doc ids to local file paths, used
  by eval/benchmarks/open_rag_bench.py to populate EvalItem.doc_ids.
"""

from __future__ import annotations

import argparse


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--subset", default="50")
    parser.add_argument("--out", default="datasets/open_rag_bench")
    args = parser.parse_args()  # noqa: F841
    raise NotImplementedError


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
