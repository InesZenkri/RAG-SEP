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
    """Scans the input text for [doc_id:pN] patterns and converts them into a list of Citation objects."""
    citations = []
    
    for match in CITATION_PATTERN.finditer(text):
        doc_id = match.group(1)
        page_num = int(match.group(2))
        
        citations.append(
            Citation(
                doc_id=doc_id,
                page=page_num,
                chunk_id=None,
                quote=None 
            )
        )
        
    return citations


def validate_citations(
    answer_text: str,
    retrieved: list[RetrievalResult],
    min_overlap: float = 0.15,
) -> list[CitationSupport]:
    raise NotImplementedError
