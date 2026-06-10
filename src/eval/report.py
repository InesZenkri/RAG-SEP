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

    snapshot = _metric_snapshot(report.get("metrics", {}))
    if snapshot:
        lines += [
            "## Metric Snapshot",
            "",
            "| Category | Metric | Value | Status |",
            "|----------|--------|-------|--------|",
        ]
        for category, metric, value in snapshot:
            lines.append(
                f"| {category} | {metric} | {_fmt(value)} | {_score_status(metric, value)} |"
            )
        lines.append("")

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
            "| id | type | retrieval | em | f1 | citation precision | issues |",
            "|----|------|-----------|----|----|--------------------|--------|",
        ]
        for item in per_item:
            lines.append(
                f"| {item.get('id', '?')} "
                f"| {item.get('type', '?')} "
                f"| {_fmt(item.get('retrieval_hit@5'))} "
                f"| {_fmt(item.get('exact_match'))} "
                f"| {_fmt(item.get('token_f1'))} "
                f"| {_fmt(item.get('citation_precision'))} "
                f"| {_escape_md(_issue_text(item))} |"
            )
        lines.append("")

        failing_items = [item for item in per_item if item.get("issues")]
        if failing_items:
            lines += ["## Per-Item Diagnostics", ""]
            for item in failing_items:
                lines += [
                    f"### {item.get('id', '?')}",
                    "",
                    f"- Question: {_escape_md(item.get('question', ''))}",
                    f"- Gold: {_escape_md(item.get('gold_answer', ''))}",
                    f"- Predicted: {_escape_md(item.get('predicted', ''))}",
                    f"- Issues: {_escape_md(_issue_text(item))}",
                    f"- Gold retrieval keys: `{', '.join(item.get('gold_retrieval_keys', []))}`",
                    f"- Top retrieved: {_format_retrieved(item.get('retrieved', []))}",
                    f"- Citations: {_format_citations(item.get('citations', []))}",
                    "",
                ]

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


def _metric_snapshot(metrics: dict[str, Any]) -> list[tuple[str, str, Any]]:
    preferred = [
        ("retrieval", "recall@5"),
        ("retrieval", "mrr"),
        ("answer", "exact_match"),
        ("answer", "token_f1"),
        ("grounding", "citation_precision"),
        ("grounding", "citation_recall"),
        ("abstention", "false_refusal_rate"),
        ("abstention", "false_answer_rate"),
    ]
    rows: list[tuple[str, str, Any]] = []
    for category, metric in preferred:
        value = metrics.get(category, {}).get(metric)
        if value is not None:
            rows.append((category, metric, value))
    return rows


def _score_status(metric: str, value: Any) -> str:
    if not isinstance(value, float):
        return "-"
    if metric in {"false_refusal_rate", "false_answer_rate"}:
        if value <= 0.1:
            return "good"
        if value <= 0.3:
            return "ok"
        return "needs work"
    if value >= 0.9:
        return "good"
    if value >= 0.7:
        return "ok"
    return "needs work"


def _issue_text(item: dict[str, Any]) -> str:
    issues = item.get("issues") or []
    if not issues:
        return "none"
    return ", ".join(issues)


def _format_retrieved(retrieved: list[dict[str, Any]]) -> str:
    if not retrieved:
        return "-"
    top = retrieved[:3]
    return ", ".join(
        f"`#{hit.get('rank')} {hit.get('doc_id')}:p{hit.get('page')} "
        f"({hit.get('score'):.3f})`"
        for hit in top
        if isinstance(hit.get("score"), (int, float))
    )


def _format_citations(citations: list[dict[str, Any]]) -> str:
    if not citations:
        return "-"
    values = []
    for citation in citations:
        key = f"{citation.get('doc_id')}:p{citation.get('page')}"
        status = "valid" if citation.get("valid_retrieved_key") else "invalid"
        values.append(f"`{key}` ({status})")
    return ", ".join(values)


def _escape_md(value: Any) -> str:
    return str(value).replace("|", "\\|")
