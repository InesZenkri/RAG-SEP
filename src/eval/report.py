"""Writes eval results to report.json and report.md."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def build_report(
    run_meta: dict[str, Any],
    metrics_by_category: dict[str, dict[str, Any]],
    per_item: list[dict[str, Any]],
) -> dict[str, Any]:
    """Combine run metadata, metrics, and per-item results into one dict."""
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "meta": run_meta,
        "metrics": metrics_by_category,
        "per_item": per_item,
    }


def write_report(report: dict[str, Any], out_dir: str | Path) -> Path:
    """Write report.json and report.md to out_dir. Returns the path to report.json."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    json_path = out / "report.json"
    json_path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")

    meta = report.get("meta", {})
    lines: list[str] = [
        f"# Eval Report — {meta.get('suite', '?')}",
        "",
        f"| Field | Value |",
        f"|-------|-------|",
        f"| Config | `{meta.get('config', '?')}` |",
        f"| Tag | {meta.get('tag') or 'untagged'} |",
        f"| Generated | {report.get('generated_at', '?')} |",
        f"| Items | {meta.get('num_items', '?')} |",
        f"| Errors | {meta.get('num_errors', 0)} |",
        "",
    ]

    for category, values in report.get("metrics", {}).items():
        lines.append(f"## {category.replace('_', ' ').title()}")
        if isinstance(values, dict):
            lines += ["| Metric | Value |", "|--------|-------|"]
            for k, v in values.items():
                if isinstance(v, float):
                    lines.append(f"| {k} | {v:.4f} |")
                elif isinstance(v, dict):
                    # nested dict e.g. avg_latency_ms broken down per stage
                    for sub_k, sub_v in v.items():
                        label = f"{k} / {sub_k}"
                        if isinstance(sub_v, float):
                            lines.append(f"| {label} | {sub_v:.2f} |")
                        else:
                            lines.append(f"| {label} | {sub_v} |")
                else:
                    lines.append(f"| {k} | {v} |")
        else:
            lines.append(str(values))
        lines.append("")

    per_item = report.get("per_item", [])
    if per_item:
        lines += [
            "## Per-Item Results",
            "",
            "| id | type | abstained | em | f1 | error |",
            "|----|------|-----------|----|----|-------|",
        ]
        for item in per_item:
            lines.append(
                f"| {item.get('id', '?')} "
                f"| {item.get('type', '?')} "
                f"| {item.get('abstained', '?')} "
                f"| {_fmt(item.get('exact_match'))} "
                f"| {_fmt(item.get('token_f1'))} "
                f"| {item.get('error', '')} |"
            )
        lines.append("")

    md_path = out / "report.md"
    md_path.write_text("\n".join(lines), encoding="utf-8")

    return json_path


def _fmt(value: Any) -> str:
    """Format a float to 4 decimal places, or return '-' if None."""
    if value is None:
        return "-"
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)
