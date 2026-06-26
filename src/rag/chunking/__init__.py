"""Chunking strategies."""

from __future__ import annotations

from rag.chunking.layout_aware import chunk_document_layout_aware
from rag.chunking.recursive import chunk_document, recursive_split
from rag.chunking.semantic import chunk_document_semantic
from rag.config import ChunkingConfig
from rag.types import Chunk, Document


def chunk_document_by_strategy(
    document: Document, config: ChunkingConfig | None = None
) -> list[Chunk]:
    config = config or ChunkingConfig()
    if config.strategy == "recursive":
        return chunk_document(document, config)
    if config.strategy == "layout_aware":
        return chunk_document_layout_aware(document, config)
    if config.strategy == "semantic":
        return chunk_document_semantic(document, config)
    raise ValueError(f"Unsupported chunking strategy: {config.strategy}")


__all__ = [
    "chunk_document",
    "chunk_document_by_strategy",
    "chunk_document_layout_aware",
    "chunk_document_semantic",
    "recursive_split",
]
