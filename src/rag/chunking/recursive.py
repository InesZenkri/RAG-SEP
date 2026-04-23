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


def recursive_split(
    text: str,
    chunk_size: int,
    chunk_overlap: int,
    separators: list[str] | None = None,
) -> list[str]:
    raise NotImplementedError


def chunk_document(
    document: Document, config: ChunkingConfig | None = None
) -> list[Chunk]:
    raise NotImplementedError
