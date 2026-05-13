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
    """Verifies the fraction of cited chunks that actually contain the words used in the answer sentence citing them"""
    if not answer.citations:
        return 0.0

    total_citations = len(answer.citations)


    chunks = {r.chunk.chunk_id: r.chunk for r in answer.retrieved}
    valid_citations = 0

    for citation in answer.citations:
        chunk = chunks.get(citation.chunk_id)
        if not chunk: 
            continue
        
        text_match = citation.quote.strip().lower() in chunk.text.lower()
        meta_match = citation.doc_id == chunk.doc_id and citation.page == chunk.page

        if text_match and meta_match:
            valid_citations += 1

    return valid_citations / total_citations


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