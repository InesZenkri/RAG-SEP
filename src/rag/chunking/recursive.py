"""Recursive character splitter with overlap.

The splitter prefers larger textual boundaries first (paragraphs, lines,
sentences, words) and falls back to fixed-width slices only when a segment is
still too large. It stays dependency-free so ingestion/chunking can run in CI
without model downloads.
"""

from __future__ import annotations

from rag.config import ChunkingConfig
from rag.types import Chunk, Document


def _split_text(text: str, chunk_size: int, separators: list[str]) -> list[str]:
    if len(text) <= chunk_size:
        return [text]

    if not separators:
        return [text[i : i + chunk_size] for i in range(0, len(text), chunk_size)]

    separator = separators[0]
    parts = text.split(separator)
    if len(parts) == 1:
        return _split_text(text, chunk_size, separators[1:])

    pieces: list[str] = []
    for index, part in enumerate(parts):
        if not part:
            continue
        piece = part if index == len(parts) - 1 else part + separator
        if len(piece) <= chunk_size:
            pieces.append(piece)
        else:
            pieces.extend(_split_text(piece, chunk_size, separators[1:]))
    return pieces


def _merge_pieces(pieces: list[str], chunk_size: int) -> list[str]:
    chunks: list[str] = []
    current = ""

    for piece in pieces:
        if not piece:
            continue

        if not current:
            current = piece
            continue

        if len(current) + len(piece) <= chunk_size:
            current += piece
        else:
            chunks.append(current.strip())
            current = piece

    if current:
        chunks.append(current.strip())

    return [chunk for chunk in chunks if chunk]


def _add_overlap(chunks: list[str], chunk_size: int, chunk_overlap: int) -> list[str]:
    if chunk_overlap <= 0 or len(chunks) <= 1:
        return chunks

    overlapped = [chunks[0]]
    for index in range(1, len(chunks)):
        previous = chunks[index - 1]
        current = chunks[index]
        available = max(chunk_size - len(current), 0)
        overlap_len = min(chunk_overlap, available, len(previous))
        prefix = previous[-overlap_len:] if overlap_len else ""
        overlapped.append((prefix + current).strip())

    return overlapped


def recursive_split(
    text: str,
    chunk_size: int,
    chunk_overlap: int,
    separators: list[str] | None = None,
) -> list[str]:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    if chunk_overlap < 0:
        raise ValueError("chunk_overlap must not be negative")
    if chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap must be smaller than chunk_size")

    text = text.strip()
    if not text:
        return []

    separators = separators or ["\n\n", "\n", ". ", " "]
    pieces = _split_text(text, chunk_size, separators)
    chunks = _merge_pieces(pieces, chunk_size)
    return _add_overlap(chunks, chunk_size, chunk_overlap)


def chunk_document(
    document: Document, config: ChunkingConfig | None = None
) -> list[Chunk]:
    cfg = config or ChunkingConfig()
    chunks: list[Chunk] = []
    chunk_number = 0

    for page_index, page_text in enumerate(document.pages, start=1):
        page_chunks = recursive_split(
            page_text,
            chunk_size=cfg.chunk_size,
            chunk_overlap=cfg.chunk_overlap,
            separators=cfg.separators,
        )
        search_from = 0
        for chunk_index, text in enumerate(page_chunks, start=1):
            start = page_text.find(text, search_from)
            if start == -1:
                start = search_from
            end = min(start + len(text), len(page_text))
            search_from = end
            chunk_number += 1

            chunks.append(
                Chunk(
                    chunk_id=f"{document.doc_id}:p{page_index}:c{chunk_index}",
                    doc_id=document.doc_id,
                    text=text,
                    page=page_index,
                    start=start,
                    end=end,
                    metadata={
                        "source": document.source,
                        "title": document.title,
                        "chunk_number": chunk_number,
                    },
                )
            )

    return chunks
