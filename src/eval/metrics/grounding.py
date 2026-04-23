"""Category 3 - Grounding / citation correctness.

- citation_precision: fraction of cited chunks that actually contain the
  informative tokens used in the answer sentence citing them.
- citation_recall: fraction of answer claims (sentences) that carry at least
  one supported citation.

Uses ``rag.generation.citation.validate_citations`` under the hood.
"""

from __future__ import annotations

from rag.types import Answer


def citation_precision(answer: Answer) -> float:
    raise NotImplementedError


def citation_recall(answer: Answer) -> float:
    raise NotImplementedError
