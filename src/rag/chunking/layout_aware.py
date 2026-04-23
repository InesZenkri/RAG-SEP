"""Layout-aware chunking (M3 extension).

Ideas:
- Prefer splitting on real layout boundaries (section headings, double newlines).
- Keep a chunk within a single column/section when possible.
- Attach ``section_title`` to Chunk.metadata for nicer citations.
"""

from __future__ import annotations

from rag.config import ChunkingConfig
from rag.types import Chunk, Document


def chunk_document_layout_aware(
    document: Document, config: ChunkingConfig | None = None
) -> list[Chunk]:
    raise NotImplementedError
