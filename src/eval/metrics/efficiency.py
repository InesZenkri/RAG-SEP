"""Category 6 - Efficiency metrics (latency, tokens, cost)."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from rag.types import Answer


@dataclass
class EfficiencySummary:
    avg_latency_ms: dict[str, float]
    p95_latency_ms: dict[str, float]
    avg_tokens: dict[str, float]
    total_cost_eur: float
    num_queries: int
    index_build_ms: float = 0.0
    peak_memory_mb: float = 0.0

    def to_dict(self) -> dict:
        return {
            "num_queries": self.num_queries,
            "index_build_ms": round(self.index_build_ms, 2),
            "avg_latency_ms": {k: round(v, 2) for k, v in self.avg_latency_ms.items()},
            "p95_latency_ms": {k: round(v, 2) for k, v in self.p95_latency_ms.items()},
            "avg_tokens": {k: round(v, 1) for k, v in self.avg_tokens.items()},
            "total_cost_eur": round(self.total_cost_eur, 6),
            "peak_memory_mb": round(self.peak_memory_mb, 1),
        }


def summarise_efficiency(
    answers: list[Answer], index_build_ms: float = 0.0
) -> EfficiencySummary:
    """Compute average and p95 latency, token counts, and total cost across all answers."""
    if not answers:
        return EfficiencySummary(
            avg_latency_ms={},
            p95_latency_ms={},
            avg_tokens={},
            total_cost_eur=0.0,
            num_queries=0,
            index_build_ms=index_build_ms,
        )

    # latency per pipeline stage
    latency_keys: set[str] = set()
    for a in answers:
        latency_keys.update(a.latency_ms.keys())

    avg_latency: dict[str, float] = {}
    p95_latency: dict[str, float] = {}
    for key in sorted(latency_keys):
        values = np.array([a.latency_ms.get(key, 0.0) for a in answers])
        avg_latency[key] = float(values.mean())
        # p95 is standard for latency reporting — avoids hiding outliers in the average
        p95_latency[key] = float(np.percentile(values, 95))

    # average token counts
    token_keys: set[str] = set()
    for a in answers:
        token_keys.update(a.tokens.keys())

    avg_tokens: dict[str, float] = {}
    for key in sorted(token_keys):
        values = np.array([float(a.tokens.get(key, 0)) for a in answers])
        avg_tokens[key] = float(values.mean())

    total_cost = sum(a.cost_eur for a in answers)

    return EfficiencySummary(
        avg_latency_ms=avg_latency,
        p95_latency_ms=p95_latency,
        avg_tokens=avg_tokens,
        total_cost_eur=total_cost,
        num_queries=len(answers),
        index_build_ms=index_build_ms,
    )
