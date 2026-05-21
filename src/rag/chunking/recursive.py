"""Recursive character splitter with overlap.

Contract:
- recursive_split(text, chunk_size, chunk_overlap, separators=None) -> list[str]
- chunk_document(document, config) -> list[Chunk] (one chunk per piece,
  annotated with doc_id, page, offsets, and metadata).

TODO (M2): implement; keep it pure-Python so it has no heavy deps.
"""

from __future__ import annotations

from rag.config import ChunkingConfig
from rag.types import Chunk, Document


def _split_long_piece(text: str, chunk_size: int) -> list[str]:
    return [text[i : i + chunk_size] for i in range(0, len(text), chunk_size)]


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
    pieces = [text]
    for separator in separators:
        next_pieces: list[str] = []
        for piece in pieces:
            if len(piece) <= chunk_size:
                next_pieces.append(piece)
                continue
            split_parts = [part.strip() for part in piece.split(separator) if part.strip()]
            if not split_parts:
                next_pieces.append(piece)
                continue
            for idx, part in enumerate(split_parts):
                suffix = separator.strip() if separator.strip() and idx < len(split_parts) - 1 else ""
                next_pieces.append(f"{part}{suffix}".strip())
        pieces = next_pieces

    chunks: list[str] = []
    current = ""
    for piece in pieces:
        if len(piece) > chunk_size:
            if current:
                chunks.append(current.strip())
                current = ""
            chunks.extend(_split_long_piece(piece, chunk_size))
            continue

        candidate = f"{current} {piece}".strip() if current else piece
        if len(candidate) <= chunk_size:
            current = candidate
        else:
            if current:
                chunks.append(current.strip())
            current = piece

    if current:
        chunks.append(current.strip())

    if chunk_overlap == 0 or len(chunks) <= 1:
        return chunks

    overlapped: list[str] = []
    previous_tail = ""
    for chunk in chunks:
        merged = f"{previous_tail} {chunk}".strip() if previous_tail else chunk
        overlapped.append(merged[-chunk_size:])
        previous_tail = chunk[-chunk_overlap:]
    return overlapped


def chunk_document(
    document: Document, config: ChunkingConfig | None = None
) -> list[Chunk]:
    cfg = config or ChunkingConfig()
    chunks: list[Chunk] = []

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
                start = 0
            end = start + len(text)
            search_from = end
            chunks.append(
                Chunk(
                    chunk_id=f"{document.doc_id}:p{page_index}:c{chunk_index}",
                    doc_id=document.doc_id,
                    text=text,
                    page=page_index,
                    start=start,
                    end=end,
                    metadata={"source": document.source, "title": document.title},
                )
            )

    return chunks
