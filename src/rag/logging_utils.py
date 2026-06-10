"""Structured JSON logging + a step timer context manager."""

from __future__ import annotations

import json
import logging
import time
from collections.abc import Iterator
from contextlib import contextmanager


class _JsonFormatter(logging.Formatter):
    """Formats log records as single-line JSON for CI pipelines."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, object] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload)


def setup_logging(level: str = "INFO", json_output: bool = False) -> None:
    """Set up the root logger. Use json_output=True in CI, False for local dev."""
    handler = logging.StreamHandler()
    if json_output:
        handler.setFormatter(_JsonFormatter())
    else:
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
                datefmt="%H:%M:%S",
            )
        )
    root = logging.getLogger()
    root.setLevel(getattr(logging, level.upper(), logging.INFO))
    root.handlers.clear()
    root.addHandler(handler)


@contextmanager
def timed(store: dict[str, float], key: str) -> Iterator[None]:
    """Records how long a block takes (in ms) and stores it in the given dict.

    Example:
        with timed(answer.latency_ms, "retrieval"):
            results = retriever.retrieve(query)
    """
    start = time.perf_counter()
    try:
        yield
    finally:
        store[key] = (time.perf_counter() - start) * 1_000.0
