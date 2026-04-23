"""Semantic chunking (M3 extension).

Group consecutive sentences whose embeddings are highly similar into the same
chunk; start a new chunk at large similarity drops. Only enable if measurement
shows it improves retrieval metrics over recursive chunking.
"""

from __future__ import annotations

from rag.config import ChunkingConfig
from rag.types import Chunk, Document


def chunk_document_semantic(
    document: Document, config: ChunkingConfig | None = None
) -> list[Chunk]:
    raise NotImplementedError
