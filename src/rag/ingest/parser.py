"""PDF and plaintext parsing with graceful fallbacks."""

from __future__ import annotations

from pathlib import Path

import fitz

from rag.config import IngestConfig
from rag.types import Document
from rag.ingest.cleaner import strip_headers_footers


def parse_text_file(path: str | Path, doc_id: str | None = None) -> Document:
    path = Path(path)
    text = path.read_text(encoding="utf-8")

    return Document(
        doc_id=doc_id or path.stem,
        source=str(path),
        title=path.stem,
        metadata={"file_type": path.suffix.lower()},
        pages=[text],
    )


def parse_pdf(path: str | Path, config: IngestConfig | None = None) -> Document:
    path = Path(path)
    raw_pages: list[str] = []

    with fitz.open(path) as pdf:
        for page in pdf:
            text = page.get_text("text")
            raw_pages.append(text)

    cleaned_pages = strip_headers_footers(raw_pages)

    return Document(
        doc_id=path.stem,
        source=str(path),
        title=path.stem,
        metadata={
            "file_type": ".pdf",
            "num_pages": len(cleaned_pages),
        },
        pages=cleaned_pages,
    )


def parse_document(path: str | Path, config: IngestConfig | None = None) -> Document:
    path = Path(path)
    suffix = path.suffix.lower()

    if suffix == ".pdf":
        return parse_pdf(path, config=config)

    if suffix in {".txt", ".md"}:
        return parse_text_file(path)

    raise ValueError(f"Unsupported document type: {suffix}")