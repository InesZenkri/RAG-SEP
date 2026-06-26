"""Layout-aware chunking.

This strategy keeps simple section boundaries visible to retrieval by grouping
text under likely headings before applying the recursive splitter.
"""

from __future__ import annotations

import re

from rag.chunking.recursive import recursive_split
from rag.config import ChunkingConfig
from rag.types import Chunk, Document

_NUMBERED_HEADING = re.compile(r"^\s*(\d+(?:\.\d+)*)\s+.+")


def _is_heading(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return False
    if len(stripped) > 90 or stripped.endswith((".", ",", ";", ":")):
        return False
    if _NUMBERED_HEADING.match(stripped):
        return True
    words = stripped.split()
    if 1 <= len(words) <= 8 and stripped[0].isupper():
        return True
    return stripped.isupper() and len(words) <= 10


def _sections(page_text: str) -> list[tuple[str | None, str, int]]:
    sections: list[tuple[str | None, str, int]] = []
    current_title: str | None = None
    current_lines: list[str] = []
    current_start = 0
    offset = 0

    for raw_line in page_text.splitlines(keepends=True):
        line = raw_line.rstrip("\n")
        if _is_heading(line):
            if current_lines:
                sections.append((current_title, "".join(current_lines).strip(), current_start))
            current_title = line.strip()
            current_lines = [raw_line]
            current_start = offset
        else:
            if not current_lines:
                current_start = offset
            current_lines.append(raw_line)
        offset += len(raw_line)

    if current_lines:
        sections.append((current_title, "".join(current_lines).strip(), current_start))

    return [(title, text, start) for title, text, start in sections if text]


def chunk_document_layout_aware(
    document: Document, config: ChunkingConfig | None = None
) -> list[Chunk]:
    config = config or ChunkingConfig()
    chunks: list[Chunk] = []
    chunk_number = 0

    for page_number, page_text in enumerate(document.pages, start=1):
        for section_index, (section_title, section_text, section_start) in enumerate(
            _sections(page_text), start=1
        ):
            section_chunks = recursive_split(
                section_text,
                chunk_size=config.chunk_size,
                chunk_overlap=config.chunk_overlap,
                separators=config.separators,
            )
            cursor = 0
            for section_chunk_index, chunk_text in enumerate(section_chunks, start=1):
                relative_start = section_text.find(chunk_text, cursor)
                if relative_start == -1:
                    relative_start = cursor
                start = section_start + relative_start
                end = min(start + len(chunk_text), len(page_text))
                cursor = relative_start + len(chunk_text)
                chunk_number += 1

                chunks.append(
                    Chunk(
                        chunk_id=(
                            f"{document.doc_id}:p{page_number}:"
                            f"s{section_index}:c{section_chunk_index}"
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
                            "section_title": section_title,
                            "chunking_strategy": "layout_aware",
                        },
                    )
                )

    return chunks
