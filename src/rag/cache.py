"""Disk-backed prompt cache to keep free-tier LLM usage cheap and reproducible.

TODO (M2):
- Hash (provider, model, system, user, temperature, max_tokens) -> JSON file on disk.
- On hit, return cached response and mark it as ``cached=True`` for traceability.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any


class PromptCache:
    def __init__(self, directory: str | Path) -> None:
        self.dir = Path(directory)
        self.dir.mkdir(parents=True, exist_ok=True)

    def get(self, key: str | dict[str, Any]) -> dict[str, Any] | None:
        path = self._path_for(key)
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None

    def set(self, key: str | dict[str, Any], value: Any) -> None:
        path = self._path_for(key)
        payload = self._to_jsonable(value)
        path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    def put(self, key: str | dict[str, Any], value: Any) -> None:
        self.set(key, value)

    def _path_for(self, key: str | dict[str, Any]) -> Path:
        if isinstance(key, dict):
            raw_key = json.dumps(key, sort_keys=True, default=str)
        else:
            raw_key = key
        digest = hashlib.sha256(raw_key.encode("utf-8")).hexdigest()
        return self.dir / f"{digest}.json"

    def _to_jsonable(self, value: Any) -> Any:
        if is_dataclass(value):
            return asdict(value)
        if isinstance(value, dict):
            return value
        return json.loads(json.dumps(value, default=str))
