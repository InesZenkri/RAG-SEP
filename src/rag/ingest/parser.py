"""PDF and plaintext parsing with graceful fallbacks."""

from __future__ import annotations

from pathlib import Path

import fitz

from rag.config import IngestConfig
from rag.ingest.cleaner import strip_headers_footers
from rag.ingest.ocr import maybe_ocr
from rag.ingest.tables import extract_tables_markdown
from rag.types import Document


def parse_text_file(path: str | Path, doc_id: str | None = None) -> Document:
    path = Path(path)
    text = path.read_text(encoding="utf-8")

    return Document(
        doc_id=doc_id or path.stem,
        source=str(path),
        title=path.stem,
        metadata={"file_type": path.suffix.lower(), "num_pages": 1},
        pages=[text],
    )


def parse_pdf(path: str | Path, config: IngestConfig | None = None) -> Document:
    path = Path(path)
    config = config or IngestConfig()
    raw_pages, parser_used, warnings = _extract_pdf_pages(path, config.parser)
    table_pages = 0

    if config.extract_tables:
        raw_pages, table_pages = _append_tables(path, raw_pages)

    ocr_applied = False
    if config.ocr and _needs_ocr(raw_pages):
        ocr_pages = maybe_ocr(path, language=config.ocr_language)
        if ocr_pages:
            raw_pages = ocr_pages
            ocr_applied = True

    pages = strip_headers_footers(raw_pages) if config.strip_headers_footers else raw_pages

    return Document(
        doc_id=path.stem,
        source=str(path),
        title=path.stem,
        metadata={
            "file_type": ".pdf",
            "num_pages": len(pages),
            "parser": parser_used,
            "parser_requested": config.parser,
            "table_extraction_enabled": config.extract_tables,
            "tables_extracted": table_pages > 0,
            "table_pages": table_pages,
            "ocr_enabled": config.ocr,
            "ocr_applied": ocr_applied,
            "extraction_warnings": warnings,
        },
        pages=pages,
    )


def parse_document(path: str | Path, config: IngestConfig | None = None) -> Document:
    path = Path(path)
    suffix = path.suffix.lower()

    if suffix == ".pdf":
        return parse_pdf(path, config=config)

    if suffix in {".txt", ".md"}:
        return parse_text_file(path)

    raise ValueError(f"Unsupported document type: {suffix}")


def _needs_ocr(pages: list[str]) -> bool:
    return bool(pages) and all(not page.strip() for page in pages)


def _extract_pdf_pages(path: Path, parser: str) -> tuple[list[str], str, list[str]]:
    parser = parser.lower()
    if parser == "pymupdf":
        return _extract_with_pymupdf(path), "pymupdf", []
    if parser == "pdfplumber":
        return _extract_with_pdfplumber(path), "pdfplumber", []
    if parser != "auto":
        raise ValueError(f"Unsupported PDF parser: {parser}")

    warnings: list[str] = []
    try:
        pages = _extract_with_pymupdf(path)
        if not _needs_ocr(pages):
            return pages, "pymupdf", warnings
        warnings.append("pymupdf returned no extractable text; tried pdfplumber fallback")
    except Exception as exc:
        warnings.append(f"pymupdf failed: {exc}")

    try:
        return _extract_with_pdfplumber(path), "pdfplumber", warnings
    except Exception as exc:
        warnings.append(f"pdfplumber failed: {exc}")
        raise ValueError(f"Could not parse PDF {path}") from exc


def _extract_with_pymupdf(path: Path) -> list[str]:
    pages: list[str] = []
    with fitz.open(path) as pdf:
        for page in pdf:
            pages.append(page.get_text("text"))
    return pages


def _extract_with_pdfplumber(path: Path) -> list[str]:
    import pdfplumber

    pages: list[str] = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            pages.append(page.extract_text() or "")
    return pages


def _append_tables(path: Path, pages: list[str]) -> tuple[list[str], int]:
    try:
        import pdfplumber
    except ImportError:
        return pages, 0

    merged = list(pages)
    table_pages = 0
    try:
        with pdfplumber.open(path) as pdf:
            for index, page in enumerate(pdf.pages):
                if index >= len(merged):
                    break
                tables = extract_tables_markdown(page)
                if tables:
                    merged[index] = f"{merged[index].rstrip()}\n\n{tables}".strip()
                    table_pages += 1
    except Exception:
        return pages, 0

    return merged, table_pages
