"""Parser tests (M2).

Planned cases:
- parse_text_file returns a 1-page Document for a .txt fixture.
- parse_pdf returns one page per PDF page using PyMuPDF.
- strip_headers_footers removes lines that repeat on >= 50% of pages.
- extract_tables_markdown renders a pdfplumber table as markdown.
"""

import pytest

pytest.skip("parser logic lands in M2", allow_module_level=True)
