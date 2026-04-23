"""Render pdfplumber tables to markdown so they become retrievable chunks.

TODO (M3):
- table_to_markdown(table): convert a 2D list to a markdown table string.
- extract_tables_markdown(page): run pdfplumber.Page.extract_tables and join.
"""

from __future__ import annotations

from typing import Any


def table_to_markdown(table: list[list[Any]]) -> str:
    raise NotImplementedError


def extract_tables_markdown(page: Any) -> str:
    raise NotImplementedError
