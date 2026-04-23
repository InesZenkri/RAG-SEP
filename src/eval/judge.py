"""LLM-as-judge for abstractive answer quality.

Contract:
- Uses a different model family than the generator (config default:
  generator = gemini-1.5-flash, judge = gemini-1.5-pro; swap to a HuggingFace
  judge for even stronger independence).
- Rubric covers: factuality, groundedness-in-cited-evidence, completeness.
- Returns a float in [0, 1] and a short free-text rationale stored in the
  run report for audit.

TODO (M5): implement; calibrate on a small human-labelled sample before use.
"""

from __future__ import annotations

from dataclasses import dataclass

from rag.generation.llm_client import LLMClient


@dataclass
class JudgeVerdict:
    score: float
    rationale: str


class LLMJudge:
    def __init__(self, client: LLMClient) -> None:
        self.client = client

    def score_answer(
        self, question: str, gold_answer: str, predicted_answer: str, context: str
    ) -> JudgeVerdict:
        raise NotImplementedError
