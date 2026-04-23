"""Abstention logic.

Refusal reasons:
- ``no_hits``: retriever returned nothing.
- ``low_retrieval_score``: top score < configured threshold.
- ``model_refusal``: the model itself emitted REFUSAL_PHRASE.
- ``contradiction``: cited chunks disagree (M5 extension, optional).

TODO (M2 base, M5 richer):
- should_abstain(retrieved, answer_text, config) -> AbstentionDecision.
"""

from __future__ import annotations

from dataclasses import dataclass

from rag.config import AbstentionConfig
from rag.types import RetrievalResult

REFUSAL_PHRASE = "I cannot answer from the provided documents."


@dataclass
class AbstentionDecision:
    abstain: bool
    reason: str
    top_score: float


def should_abstain(
    retrieved: list[RetrievalResult],
    answer_text: str | None,
    config: AbstentionConfig,
) -> AbstentionDecision:
    raise NotImplementedError
