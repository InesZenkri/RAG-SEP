"""Disk-backed prompt cache to keep free-tier LLM usage cheap and reproducible.

TODO (M2):
- Hash (provider, model, system, user, temperature, max_tokens) -> JSON file on disk.
- On hit, return cached response and mark it as ``cached=True`` for traceability.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


class PromptCache:
    def __init__(self, directory: str | Path) -> None:
        self.dir = Path(directory)

    def get(self, payload: dict[str, Any]) -> dict[str, Any] | None:
        raise NotImplementedError

    def put(self, payload: dict[str, Any], value: dict[str, Any]) -> None:
        raise NotImplementedError
