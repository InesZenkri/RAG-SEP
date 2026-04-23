"""Category 6 - Efficiency.

Aggregate per-query latency breakdown (retrieve / rerank / generate), tokens
in/out, and euro cost across an eval run. Also records index build time and
peak memory so the efficiency table in the final report is one function call
away.
"""

from __future__ import annotations

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


def summarise_efficiency(
    answers: list[Answer], index_build_ms: float = 0.0
) -> EfficiencySummary:
    raise NotImplementedError
