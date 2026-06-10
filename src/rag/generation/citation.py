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

CITATION_PATTERN = re.compile(r"<?([A-Za-z0-9_\-]+):p(\d+)>?")


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
                    quote=None,
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
                quote=None,
            )
        )

    return citations


def _citation_markers(citation: Citation) -> set[str]:
    return {
        f"[{citation.doc_id}:p{citation.page}]",
        f"[<{citation.doc_id}:p{citation.page}>]",
    }


def validate_citations(
    answer_text: str,
    retrieved: list[RetrievalResult],
    min_overlap: float = 0.15,
) -> list[CitationSupport]:
    """verifies for each citation, that the cited chunk contains enough informative tokens from the sentence that cites it"""
    stops = {"the", "and", "for", "are", "was", "but", "with", "that", "this", "from"}

    by_key = {result.chunk.citation_key(): result.chunk for result in retrieved}
    citation_list: list[CitationSupport] = []

    raw_sentences = re.split(r"(?<=[.!?]) +", answer_text)

    for citation in extract_citations(answer_text):
        chunk = by_key.get(citation.key())
        markers = _citation_markers(citation)

        citing_sentence = answer_text
        for sentence in raw_sentences:
            if any(marker in sentence for marker in markers):
                citing_sentence = sentence
                break

        claim_text = re.sub(r"\[[^\]]*\]", "", citing_sentence)
        raw_claim_words = re.findall(r"\b\w{3,}\b", claim_text.lower())

        claim_tokens = {word for word in raw_claim_words if word not in stops}

        if chunk:
            chunk_tokens = set(re.findall(r"\b\w{3,}\b", chunk.text.lower()))
        else:
            chunk_tokens = set()

        if not claim_tokens:
            overlap = 0.0
        else:
            matching_tokens = claim_tokens & chunk_tokens
            overlap = len(matching_tokens) / len(claim_tokens)

        is_supported = (chunk is not None) and (overlap >= min_overlap)

        citation_list.append(
            CitationSupport(citation, is_supported, overlap)
        )

    return citation_list
