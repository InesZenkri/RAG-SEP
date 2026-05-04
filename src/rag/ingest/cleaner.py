from __future__ import annotations

from collections import Counter


def strip_headers_footers(
    pages: list[str],
    window: int = 2,
    min_repeat_ratio: float = 0.5,
) -> list[str]:

    if not pages:
        return []

    line_counts = Counter()
    total_pages = len(pages)

    for page in pages:
        lines = page.split("\n")
        candidates = lines[:window] + lines[-window:]

        for line in candidates:
            cleaned = line.strip()
            if cleaned:
                line_counts[cleaned] += 1

    repeated = {
        line
        for line, count in line_counts.items()
        if count / total_pages >= min_repeat_ratio
    }

    cleaned_pages = []

    for page in pages:
        lines = page.split("\n")
        filtered = [line for line in lines if line.strip() not in repeated]
        cleaned_pages.append("\n".join(filtered))

    return cleaned_pages
