"""Citation extraction + validation.

Contract (M2 extract, M5 validate):
- extract_citations(text): pull ``[doc_id:pN]`` markers out of an answer in order.
- validate_citations(answer, retrieved): for each citation, check that the
  cited chunk contains enough informative tokens from the sentence that cites
  it. Lightweight proxy for NLI-based grounding.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from rag.types import Citation, RetrievalResult

CITATION_PATTERN = re.compile(r"\[([A-Za-z0-9_\-]+):p(\d+)\]")


@dataclass
class CitationSupport:
    citation: Citation
    supported: bool
    overlap: float


def extract_citations(text: str) -> list[Citation]:
    raise NotImplementedError


def validate_citations(
    answer_text: str,
    retrieved: list[RetrievalResult],
    min_overlap: float = 0.15,
) -> list[CitationSupport]:
    raise NotImplementedError
