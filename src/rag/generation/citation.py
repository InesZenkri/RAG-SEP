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

CITATION_PATTERN = re.compile(r"([A-Za-z0-9_\-]+):p(\d+)")


@dataclass
class CitationSupport:
    citation: Citation
    supported: bool
    overlap: float


def extract_citations(text: str) -> list[Citation]:
    """Scans the input text for [doc_id:pN] patterns and converts them into a list of Citation objects."""
    citations = []

    for bracket in re.finditer(r"\[([^\]]+)\]", text):
        for match in CITATION_PATTERN.finditer(bracket.group(1)):
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

    if citations:
        return citations

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
    by_key = {r.chunk.citation_key(): r.chunk for r in retrieved}
    out: list[CitationSupport] = []
    for cit in extract_citations(answer_text):
        chunk = by_key.get(cit.key())
        marker = f"[{cit.doc_id}:p{cit.page}]"
        sentence = next((s for s in re.split(r"(?<=[.!?]) +", answer_text) if marker in s), answer_text)
        claim = re.sub(r"\[[^\]]*\]", "", sentence)
        claim_tokens = {w for w in re.findall(r"\b\w{3,}\b", claim.lower())}
        chunk_tokens = {w for w in re.findall(r"\b\w{3,}\b", chunk.text.lower())} if chunk else set()
        overlap = len(claim_tokens & chunk_tokens) / len(claim_tokens) if claim_tokens else 0.0
        out.append(CitationSupport(cit, chunk is not None and overlap >= min_overlap, overlap))
    return out
