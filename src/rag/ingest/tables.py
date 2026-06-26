"""Render pdfplumber tables to markdown so they become retrievable chunks."""

from __future__ import annotations

from typing import Any


def table_to_markdown(table: list[list[Any]]) -> str:
    rows = [
        ["" if cell is None else str(cell).replace("\n", " ").strip() for cell in row]
        for row in table
        if row and any(cell is not None and str(cell).strip() for cell in row)
    ]
    if not rows:
        return ""

    width = max(len(row) for row in rows)
    normalised = [row + [""] * (width - len(row)) for row in rows]
    header = normalised[0]
    separator = ["---"] * width
    body = normalised[1:]

    markdown_rows = [header, separator, *body]
    return "\n".join("| " + " | ".join(row) + " |" for row in markdown_rows)


def extract_tables_markdown(page: Any) -> str:
    tables = page.extract_tables() or []
    rendered = [table_to_markdown(table) for table in tables]
    return "\n\n".join(table for table in rendered if table)
