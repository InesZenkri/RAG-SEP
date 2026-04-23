"""Category 2 - Answer quality.

For extractive questions: normalised Exact-Match and token-level F1
(SQuAD-style normalisation: lowercase, strip punctuation/articles, collapse
whitespace).

For abstractive / long-form questions: delegated to
``eval.judge.LLMJudge.score_answer`` using a different model family than the
generator to reduce bias.
"""

from __future__ import annotations


def normalize(text: str) -> str:
    raise NotImplementedError


def exact_match(prediction: str, references: list[str]) -> float:
    raise NotImplementedError


def token_f1(prediction: str, references: list[str]) -> float:
    raise NotImplementedError
