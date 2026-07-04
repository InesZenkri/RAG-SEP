"""Abstention logic.

Refusal reasons:
- ``no_hits``: retriever returned nothing.
- ``low_retrieval_score``: top score < configured threshold.
- ``model_refusal``: the model itself emitted REFUSAL_PHRASE.
- ``contradiction``: cited chunks disagree (M5 extension, optional)."""

from __future__ import annotations

from dataclasses import dataclass

from rag.config import AbstentionConfig
from rag.generation.citation import CitationSupport
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
    citation_supports: list[CitationSupport] | None = None,
) -> AbstentionDecision:
    """Evaluates if the system should abstain from answering"""

    top_score = max((r.score for r in retrieved), default=0.0)

    if not config.enabled:
        return AbstentionDecision(
            abstain=False,
            reason="disabled",
            top_score=top_score
        )

    if not retrieved:
        return AbstentionDecision(
            abstain=True,
            reason="no_hits",
            top_score=0.0
        )

    if top_score < config.min_retrieval_score:
        return AbstentionDecision(
            abstain=True,
            reason="low_retrieval_score",
            top_score=top_score
        )

    if answer_text is not None and REFUSAL_PHRASE in answer_text:
        return AbstentionDecision(
            abstain=True,
            reason="model_refusal",
            top_score=top_score
        )

    if answer_text is not None and config.min_citations > 0 and citation_supports is not None:
        supported_citations = sum(1 for support in citation_supports if support.supported)
        if supported_citations < config.min_citations:
            return AbstentionDecision(
                abstain=True,
                reason="missing_citations",
                top_score=top_score,
            )

    return AbstentionDecision(
        abstain=False,
        reason="success",
        top_score=top_score
    )
