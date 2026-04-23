"""Retriever protocol shared by dense, lexical, and hybrid implementations."""

from __future__ import annotations

from abc import ABC, abstractmethod

from rag.types import Chunk, RetrievalResult


class Retriever(ABC):
    """All retrievers expose the same two-step API: index() then query()."""

    name: str = "retriever"

    @abstractmethod
    def index(self, chunks: list[Chunk]) -> None: ...

    @abstractmethod
    def query(self, text: str, top_k: int) -> list[RetrievalResult]: ...

    def __len__(self) -> int:  # pragma: no cover
        return 0
