import sys
import types
from pathlib import Path

import fitz
import pytest

from rag.config import IngestConfig
from rag.ingest.cleaner import strip_headers_footers
from rag.ingest.ocr import maybe_ocr
from rag.ingest.parser import parse_document, parse_pdf, parse_text_file
from rag.ingest.tables import extract_tables_markdown, table_to_markdown


def test_parse_text_file_returns_one_page(tmp_path: Path) -> None:
    source = tmp_path / "note.txt"
    source.write_text("hello from a text file", encoding="utf-8")

    document = parse_text_file(source)

    assert document.doc_id == "note"
    assert document.source == str(source)
    assert document.pages == ["hello from a text file"]
    assert document.metadata["file_type"] == ".txt"


def test_parse_document_dispatches_text_files(tmp_path: Path) -> None:
    source = tmp_path / "note.md"
    source.write_text("# heading", encoding="utf-8")

    document = parse_document(source)

    assert document.title == "note"
    assert document.pages == ["# heading"]


def test_parse_pdf_returns_pages(tmp_path: Path) -> None:
    sample = tmp_path / "sample.pdf"
    pdf = fitz.open()
    page = pdf.new_page()
    page.insert_text((72, 72), "Hello PDF")
    pdf.save(sample)
    pdf.close()

    document = parse_pdf(sample)

    assert document.doc_id == "sample"
    assert document.metadata["file_type"] == ".pdf"
    assert document.num_pages >= 1
    assert any(page.strip() for page in document.pages)
    assert document.metadata["parser"] == "pymupdf"
    assert document.metadata["parser_requested"] == "pymupdf"


def test_parse_pdf_respects_header_footer_config(monkeypatch, tmp_path: Path) -> None:
    source = tmp_path / "fake.pdf"
    source.write_bytes(b"%PDF fake")

    class FakePage:
        def __init__(self, text: str) -> None:
            self.text = text

        def get_text(self, mode: str) -> str:
            assert mode == "text"
            return self.text

    class FakePdf:
        def __iter__(self):
            return iter(
                [
                    FakePage("HEADER\npage one\nFOOTER"),
                    FakePage("HEADER\npage two\nFOOTER"),
                ]
            )

        def __enter__(self):
            return self

        def __exit__(self, *args) -> None:
            return None

    def fake_open(path: Path):
        return FakePdf()

    monkeypatch.setattr("rag.ingest.parser.fitz.open", fake_open)

    document = parse_pdf(source, IngestConfig(strip_headers_footers=True))

    assert document.pages == ["page one", "page two"]


def test_strip_headers_footers_removes_repeated_edges() -> None:
    pages = [
        "HEADER\ncontent one\nFOOTER",
        "HEADER\ncontent two\nFOOTER",
        "HEADER\ncontent three\nFOOTER",
    ]

    cleaned = strip_headers_footers(pages, window=1)

    assert cleaned == ["content one", "content two", "content three"]


def test_table_to_markdown() -> None:
    table = [["Name", "Score"], ["Alice", 10], ["Bob", None]]

    markdown = table_to_markdown(table)

    assert "| Name | Score |" in markdown
    assert "| --- | --- |" in markdown
    assert "| Alice | 10 |" in markdown
    assert "| Bob |  |" in markdown


def test_extract_tables_markdown_from_page() -> None:
    class FakePage:
        def extract_tables(self):
            return [[["Name", "Score"], ["Alice", "10"]]]

    markdown = extract_tables_markdown(FakePage())

    assert "| Name | Score |" in markdown
    assert "| Alice | 10 |" in markdown


def test_parse_pdf_appends_tables_when_configured(monkeypatch, tmp_path: Path) -> None:
    source = tmp_path / "fake.pdf"
    source.write_bytes(b"%PDF fake")

    class FakePage:
        def get_text(self, mode: str) -> str:
            return "Body text"

    class FakePdf:
        def __iter__(self):
            return iter([FakePage()])

        def __enter__(self):
            return self

        def __exit__(self, *args) -> None:
            return None

    class FakePdfPlumberPage:
        def extract_tables(self):
            return [[["Column"], ["Value"]]]

    class FakePdfPlumber:
        pages = [FakePdfPlumberPage()]

        def __enter__(self):
            return self

        def __exit__(self, *args) -> None:
            return None

    fake_pdfplumber = types.SimpleNamespace(open=lambda path: FakePdfPlumber())

    monkeypatch.setattr("rag.ingest.parser.fitz.open", lambda path: FakePdf())
    monkeypatch.setitem(sys.modules, "pdfplumber", fake_pdfplumber)

    document = parse_pdf(source, IngestConfig(extract_tables=True))

    assert "Body text" in document.pages[0]
    assert "| Column |" in document.pages[0]
    assert document.metadata["tables_extracted"] is True
    assert document.metadata["table_pages"] == 1


def test_parse_pdf_uses_pdfplumber_when_configured(monkeypatch, tmp_path: Path) -> None:
    source = tmp_path / "fake.pdf"
    source.write_bytes(b"%PDF fake")

    class FakePdfPlumberPage:
        def extract_text(self):
            return "Text from pdfplumber"

    class FakePdfPlumber:
        pages = [FakePdfPlumberPage()]

        def __enter__(self):
            return self

        def __exit__(self, *args) -> None:
            return None

    fake_pdfplumber = types.SimpleNamespace(open=lambda path: FakePdfPlumber())
    monkeypatch.setitem(sys.modules, "pdfplumber", fake_pdfplumber)

    document = parse_pdf(source, IngestConfig(parser="pdfplumber"))

    assert document.pages == ["Text from pdfplumber"]
    assert document.metadata["parser"] == "pdfplumber"


def test_parse_pdf_auto_falls_back_to_pdfplumber_when_pymupdf_has_no_text(
    monkeypatch, tmp_path: Path
) -> None:
    source = tmp_path / "fake.pdf"
    source.write_bytes(b"%PDF fake")

    class EmptyPage:
        def get_text(self, mode: str) -> str:
            return ""

    class FakeFitzPdf:
        def __iter__(self):
            return iter([EmptyPage()])

        def __enter__(self):
            return self

        def __exit__(self, *args) -> None:
            return None

    class FakePdfPlumberPage:
        def extract_text(self):
            return "Fallback text"

    class FakePdfPlumber:
        pages = [FakePdfPlumberPage()]

        def __enter__(self):
            return self

        def __exit__(self, *args) -> None:
            return None

    fake_pdfplumber = types.SimpleNamespace(open=lambda path: FakePdfPlumber())
    monkeypatch.setattr("rag.ingest.parser.fitz.open", lambda path: FakeFitzPdf())
    monkeypatch.setitem(sys.modules, "pdfplumber", fake_pdfplumber)

    document = parse_pdf(source, IngestConfig(parser="auto"))

    assert document.pages == ["Fallback text"]
    assert document.metadata["parser"] == "pdfplumber"
    assert document.metadata["extraction_warnings"]


def test_maybe_ocr_returns_empty_when_dependencies_missing(monkeypatch, tmp_path: Path) -> None:
    source = tmp_path / "empty.pdf"
    source.write_bytes(b"%PDF fake")
    original_import = __import__

    def fake_import(name, *args, **kwargs):
        if name == "pytesseract":
            raise ImportError("not installed")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr("builtins.__import__", fake_import)

    assert maybe_ocr(source) == []


def test_maybe_ocr_uses_tesseract_when_available(monkeypatch, tmp_path: Path) -> None:
    source = tmp_path / "scan.pdf"
    source.write_bytes(b"%PDF fake")

    class FakePixmap:
        width = 1
        height = 1
        samples = b"\x00\x00\x00"

    class FakePage:
        def get_pixmap(self, matrix, alpha: bool):
            return FakePixmap()

    class FakePdf:
        def __iter__(self):
            return iter([FakePage()])

        def __enter__(self):
            return self

        def __exit__(self, *args) -> None:
            return None

    fake_fitz = types.SimpleNamespace(
        open=lambda path: FakePdf(),
        Matrix=lambda x, y: ("matrix", x, y),
    )
    fake_tesseract = types.SimpleNamespace(image_to_string=lambda image, lang: "OCR text")

    class FakeImage:
        @staticmethod
        def frombytes(mode, size, samples):
            return {"mode": mode, "size": size, "samples": samples}

    fake_pil = types.ModuleType("PIL")
    fake_pil_image = types.ModuleType("PIL.Image")
    fake_pil_image.frombytes = FakeImage.frombytes
    fake_pil.Image = fake_pil_image

    monkeypatch.setitem(sys.modules, "fitz", fake_fitz)
    monkeypatch.setitem(sys.modules, "pytesseract", fake_tesseract)
    monkeypatch.setitem(sys.modules, "PIL", fake_pil)
    monkeypatch.setitem(sys.modules, "PIL.Image", fake_pil_image)

    assert maybe_ocr(source) == ["OCR text"]


def test_pdfplumber_extracts_table_from_real_pdf(tmp_path: Path) -> None:
    pdfplumber = pytest.importorskip("pdfplumber")
    source = tmp_path / "table.pdf"
    pdf = fitz.open()
    page = pdf.new_page()
    page.draw_line((72, 72), (272, 72))
    page.draw_line((72, 112), (272, 112))
    page.draw_line((72, 152), (272, 152))
    page.draw_line((72, 72), (72, 152))
    page.draw_line((172, 72), (172, 152))
    page.draw_line((272, 72), (272, 152))
    page.insert_text((82, 96), "Name")
    page.insert_text((182, 96), "Score")
    page.insert_text((82, 136), "Alice")
    page.insert_text((182, 136), "10")
    pdf.save(source)
    pdf.close()

    with pdfplumber.open(source) as pdf_doc:
        markdown = extract_tables_markdown(pdf_doc.pages[0])

    assert "| Name | Score |" in markdown
    assert "| Alice | 10 |" in markdown
