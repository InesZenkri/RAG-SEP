"""Structured JSON logging + a step timer context manager.

TODO (M0 -> M2):
- setup_logging(): configure root logger with JSON or console handler.
- timed(store, key): context manager that writes elapsed ms into ``store[key]``.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator


def setup_logging(level: str = "INFO", json_output: bool = False) -> None:
    raise NotImplementedError


@contextmanager
def timed(store: dict[str, float], key: str) -> Iterator[None]:
    raise NotImplementedError
    yield  # pragma: no cover
