"""Category 6 - Efficiency metrics (latency, tokens, cost)."""

from __future__ import annotations

import math
from dataclasses import dataclass

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


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _percentile(values: list[float], percentile: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    rank = (len(ordered) - 1) * percentile / 100
    lower = math.floor(rank)
    upper = math.ceil(rank)
    if lower == upper:
        return ordered[int(rank)]
    weight = rank - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight


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
        values = [a.latency_ms.get(key, 0.0) for a in answers]
        avg_latency[key] = _mean(values)
        # p95 is standard for latency reporting — avoids hiding outliers in the average
        p95_latency[key] = _percentile(values, 95)

    # average token counts
    token_keys: set[str] = set()
    for a in answers:
        token_keys.update(a.tokens.keys())

    avg_tokens: dict[str, float] = {}
    for key in sorted(token_keys):
        values = [float(a.tokens.get(key, 0)) for a in answers]
        avg_tokens[key] = _mean(values)

    total_cost = sum(a.cost_eur for a in answers)

    return EfficiencySummary(
        avg_latency_ms=avg_latency,
        p95_latency_ms=p95_latency,
        avg_tokens=avg_tokens,
        total_cost_eur=total_cost,
        num_queries=len(answers),
        index_build_ms=index_build_ms,
    )
