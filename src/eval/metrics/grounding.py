"""Category 3 - Grounding / citation correctness.

- citation_precision: fraction of cited chunks that actually contain the
  informative tokens used in the answer sentence citing them.
- citation_recall: fraction of answer claims (sentences) that carry at least
  one supported citation.

Uses ``rag.generation.citation.validate_citations`` under the hood.
"""

from __future__ import annotations

import re

from rag.types import Answer


def citation_precision(answer: Answer):
    """Fraction of extracted citations supported by the retrieved chunks."""
    if not answer.citations:
        return 0.0

    stops = {"the", "and", "for", "are", "was", "but", "with", "that", "this", "from"}
    chunks = {result.chunk.citation_key(): result.chunk for result in answer.retrieved}
    sentences = [s for s in re.split(r"(?<=[.!?]) +", answer.text) if s.strip()]
    valid_citations = 0

    for citation in answer.citations:
        chunk = chunks.get(citation.key())
        if not chunk:
            continue

        marker = f"[{citation.doc_id}:p{citation.page}]"
        marker_index = next(
            (index for index, sentence in enumerate(sentences) if marker in sentence),
            None,
        )
        if marker_index is None:
            citing_sentence = answer.text
        elif marker_index > 0 and not re.sub(r"\[[^\]]*\]", "", sentences[marker_index]).strip():
            citing_sentence = sentences[marker_index - 1]
        else:
            citing_sentence = sentences[marker_index]
        claim_text = re.sub(r"\[[^\]]*\]", "", citing_sentence)
        claim_tokens = {
            token
            for token in re.findall(r"\b\w{3,}\b", claim_text.lower())
            if token not in stops
        }
        chunk_tokens = set(re.findall(r"\b\w{3,}\b", chunk.text.lower()))

        if claim_tokens and len(claim_tokens & chunk_tokens) / len(claim_tokens) >= 0.15:
            valid_citations += 1

    return valid_citations / len(answer.citations)


def citation_recall(answer: Answer):
    """Checks the fraction of answer sentences that carry at least one supported citation."""
    sentences = [s for s in re.split(r'(?<=[.!?]) +', answer.text) if s.strip()]
    
    if not sentences:
        return 1.0 if not answer.citations else 0.0

    total_sentences = len(sentences)
    valid_sentences = 0

    for sentence in sentences:
        is_supported = False
        
        for citation in answer.citations:
            id_match = citation.doc_id and citation.doc_id in sentence
            quote_match = citation.quote and citation.quote in sentence
            
            if id_match or quote_match:
                is_supported = True
                break

        if is_supported:
            valid_sentences += 1

    return valid_sentences / total_sentences
