"""Eval report rendering.

Two outputs per run, written under ``reports/runs/<timestamp>/``:
- ``report.json`` for machine consumption (CI regression diff).
- ``report.md``   for humans (dropped into the final written report).

TODO (M1):
- build_report(run_meta, metrics_by_category, per_item) -> dict
- write_report(report, out_dir): write both JSON and Markdown.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


def build_report(
    run_meta: dict[str, Any],
    metrics_by_category: dict[str, dict[str, float]],
    per_item: list[dict[str, Any]],
) -> dict[str, Any]:
    raise NotImplementedError


def write_report(report: dict[str, Any], out_dir: str | Path) -> Path:
    raise NotImplementedError
