"""Pydantic request/response schemas for the HTTP API."""

from __future__ import annotations

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1)
    top_k: int | None = None


class CitationSchema(BaseModel):
    doc_id: str
    page: int
    chunk_id: str | None = None
    quote: str | None = None


class QueryResponse(BaseModel):
    question: str
    answer: str
    citations: list[CitationSchema]
    confidence: float
    abstained: bool
    latency_ms: dict[str, float]
    tokens: dict[str, int]
    cost_eur: float


class IndexRequest(BaseModel):
    paths: list[str]


class IndexResponse(BaseModel):
    documents: int
    chunks: int
    pages: int
