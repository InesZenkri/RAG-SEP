"""Pydantic request/response schemas for the HTTP API."""

from __future__ import annotations

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1)
    top_k: int | None = None
    history: list[dict[str, str]] = Field(default_factory=list)


class CitationSchema(BaseModel):
    doc_id: str
    page: int
    chunk_id: str | None = None
    quote: str | None = None
    source: str | None = None
    title: str | None = None
    page_text: str | None = None
    chunk_text: str | None = None
    page_image: str | None = None


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


class ChunkSchema(BaseModel):
    chunk_id: str
    page: int
    start: int
    end: int
    text: str


class DocumentSchema(BaseModel):
    doc_id: str
    title: str | None = None
    source: str
    pages: int
    chunks: int
    chunk_details: list[ChunkSchema] = Field(default_factory=list)
