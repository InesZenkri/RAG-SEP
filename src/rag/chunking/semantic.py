"""Lightweight semantic chunking.

This implementation avoids embedding downloads. It groups adjacent sentences
while they share enough informative tokens and falls back to recursive splitting
for oversized groups.
"""

from __future__ import annotations

import re

from rag.chunking.recursive import recursive_split
from rag.config import ChunkingConfig
from rag.types import Chunk, Document

_SENTENCE_RE = re.compile(r"[^.!?]+[.!?]?")
_TOKEN_RE = re.compile(r"[A-Za-z0-9]+")
_STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "that",
    "the",
    "to",
    "with",
}


def _sentences(text: str) -> list[str]:
    return [match.group(0).strip() for match in _SENTENCE_RE.finditer(text) if match.group(0).strip()]


def _tokens(text: str) -> set[str]:
    return {
        token.lower()
        for token in _TOKEN_RE.findall(text)
        if len(token) > 2 and token.lower() not in _STOPWORDS
    }


def _similarity(left: str, right: str) -> float:
    left_tokens = _tokens(left)
    right_tokens = _tokens(right)
    if not left_tokens or not right_tokens:
        return 0.0
    return len(left_tokens & right_tokens) / len(left_tokens | right_tokens)


def _semantic_groups(text: str, chunk_size: int) -> list[str]:
    sentences = _sentences(text)
    if not sentences:
        return []

    groups: list[str] = []
    current = sentences[0]
    current_tokens = _tokens(current)

    for sentence in sentences[1:]:
        candidate = f"{current} {sentence}".strip()
        similar = _similarity(" ".join(sorted(current_tokens)), sentence) >= 0.08
        if len(candidate) <= chunk_size and similar:
            current = candidate
            current_tokens |= _tokens(sentence)
        else:
            groups.append(current)
            current = sentence
            current_tokens = _tokens(sentence)

    groups.append(current)
    return groups


def chunk_document_semantic(
    document: Document, config: ChunkingConfig | None = None
) -> list[Chunk]:
    config = config or ChunkingConfig()
    chunks: list[Chunk] = []
    chunk_number = 0

    for page_number, page_text in enumerate(document.pages, start=1):
        groups = _semantic_groups(page_text, config.chunk_size)
        if not groups:
            groups = recursive_split(
                page_text,
                chunk_size=config.chunk_size,
                chunk_overlap=config.chunk_overlap,
                separators=config.separators,
            )

        cursor = 0
        for group_index, group in enumerate(groups, start=1):
            group_chunks = recursive_split(
                group,
                chunk_size=config.chunk_size,
                chunk_overlap=config.chunk_overlap,
                separators=config.separators,
            )
            for group_chunk_index, chunk_text in enumerate(group_chunks, start=1):
                start = page_text.find(chunk_text, cursor)
                if start == -1:
                    start = cursor
                end = min(start + len(chunk_text), len(page_text))
                cursor = end
                chunk_number += 1

                chunks.append(
                    Chunk(
                        chunk_id=(
                            f"{document.doc_id}:p{page_number}:"
                            f"g{group_index}:c{group_chunk_index}"
                        ),
                        doc_id=document.doc_id,
                        text=chunk_text,
                        page=page_number,
                        start=start,
                        end=end,
                        metadata={
                            "source": document.source,
                            "title": document.title,
                            "chunk_number": chunk_number,
                            "semantic_group": group_index,
                            "chunking_strategy": "semantic",
                        },
                    )
                )

    return chunks
