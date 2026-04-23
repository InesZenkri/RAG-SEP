"""Optional OCR fallback for scanned PDFs (requires Tesseract + pytesseract).

TODO (M3):
- Render each PDF page to an image via PyMuPDF.
- Run pytesseract.image_to_string per page, return list[str].
- Return [] if pytesseract / Tesseract binary is unavailable so callers can fall back.
"""

from __future__ import annotations

from pathlib import Path


def maybe_ocr(path: str | Path, language: str = "eng") -> list[str]:
    raise NotImplementedError
