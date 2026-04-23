"""Core dataclasses shared across the pipeline.

Keeping these lightweight and pickle-friendly so the same objects can travel
through ingestion, retrieval, generation, and evaluation without glue code.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Document:
    """A source document (one PDF file after parsing)."""

    doc_id: str
    source: str  # original file path or URL
    title: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    pages: list[str] = field(default_factory=list)

    @property
    def num_pages(self) -> int:
        return len(self.pages)


@dataclass(frozen=True)
class Chunk:
    """A retrievable unit of text tied back to its source document and page."""

    chunk_id: str
    doc_id: str
    text: str
    page: int
    # optional positional info (start/end char offsets within the page)
    start: int = 0
    end: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

    def citation_key(self) -> str:
        return f"{self.doc_id}:p{self.page}"


@dataclass(frozen=True)
class RetrievalResult:
    """A ranked hit returned by a retriever."""

    chunk: Chunk
    score: float
    rank: int
    retriever: str = "unknown"


@dataclass(frozen=True)
class Citation:
    """A single citation produced by the generator."""

    doc_id: str
    page: int
    chunk_id: str | None = None
    quote: str | None = None

    def key(self) -> str:
        return f"{self.doc_id}:p{self.page}"


@dataclass
class Answer:
    """The final answer returned to the user."""

    question: str
    text: str
    citations: list[Citation] = field(default_factory=list)
    confidence: float = 0.0
    abstained: bool = False
    # retrieval / generation diagnostics
    retrieved: list[RetrievalResult] = field(default_factory=list)
    latency_ms: dict[str, float] = field(default_factory=dict)
    tokens: dict[str, int] = field(default_factory=dict)
    cost_eur: float = 0.0
    trace: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "question": self.question,
            "text": self.text,
            "citations": [
                {"doc_id": c.doc_id, "page": c.page, "chunk_id": c.chunk_id, "quote": c.quote}
                for c in self.citations
            ],
            "confidence": self.confidence,
            "abstained": self.abstained,
            "retrieved": [
                {
                    "chunk_id": r.chunk.chunk_id,
                    "doc_id": r.chunk.doc_id,
                    "page": r.chunk.page,
                    "score": r.score,
                    "rank": r.rank,
                    "retriever": r.retriever,
                }
                for r in self.retrieved
            ],
            "latency_ms": self.latency_ms,
            "tokens": self.tokens,
            "cost_eur": self.cost_eur,
            "trace": self.trace,
        }
