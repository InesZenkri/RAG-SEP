"""Optional OCR fallback for scanned PDFs.

The function is deliberately best-effort: missing optional dependencies or a
missing Tesseract binary result in ``[]`` so callers can continue with normal
text extraction.
"""

from __future__ import annotations

from pathlib import Path


def maybe_ocr(path: str | Path, language: str = "eng") -> list[str]:
    try:
        import fitz
        import pytesseract
        from PIL import Image
    except ImportError:
        return []

    pages: list[str] = []
    try:
        with fitz.open(Path(path)) as pdf:
            for page in pdf:
                pixmap = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
                image = Image.frombytes(
                    "RGB",
                    (pixmap.width, pixmap.height),
                    pixmap.samples,
                )
                pages.append(pytesseract.image_to_string(image, lang=language).strip())
    except Exception:
        return []

    return pages
