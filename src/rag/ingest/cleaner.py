"""Repeated header/footer detection and stripping across pages.

Heuristic (M3): compare the first/last N lines of each page; any line that
appears on >= 50% of pages is treated as a running header/footer and removed.
"""

from __future__ import annotations


def strip_headers_footers(
    pages: list[str],
    window: int = 2,
    min_repeat_ratio: float = 0.5,
) -> list[str]:
    raise NotImplementedError
