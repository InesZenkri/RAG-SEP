"""PDF and plaintext parsing with graceful fallbacks.

Design contract:
- Primary PDF parser: PyMuPDF (fast, good layout).
- Fallback for tables / table-aware mode: pdfplumber.
- Plaintext ``.txt`` / ``.md`` supported natively (tests, sample corpus).
- If ``IngestConfig.ocr`` is set and text extraction looks empty, run OCR.

TODO (M2 -> M3):
- Implement parse_pdf using the chosen backend per IngestConfig.
- Implement parse_text_file for plaintext fixtures.
- parse_document dispatches by file extension.
"""

from __future__ import annotations

from pathlib import Path

from rag.config import IngestConfig
from rag.types import Document


def parse_text_file(path: str | Path, doc_id: str | None = None) -> Document:
    raise NotImplementedError


def parse_pdf(path: str | Path, config: IngestConfig | None = None) -> Document:
    raise NotImplementedError


def parse_document(path: str | Path, config: IngestConfig | None = None) -> Document:
    raise NotImplementedError
