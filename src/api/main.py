"""FastAPI app exposing the RAG pipeline.

Endpoints:
- POST /index  -> ingest a list of file paths into the pipeline.
- POST /query  -> run a question through the pipeline.
- GET  /stats  -> corpus statistics (docs/chunks/pages).
- GET  /health -> liveness probe for CI/UI.

TODO (M6): implement using a module-level RAGPipeline singleton loaded from
``configs/baseline.yaml`` at startup.
"""

from __future__ import annotations

from fastapi import FastAPI

from api.schemas import (
    IndexRequest,
    IndexResponse,
    QueryRequest,
    QueryResponse,
)

app = FastAPI(title="Reliable PDF Search Agent", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/stats")
def stats() -> dict[str, int]:
    raise NotImplementedError


@app.post("/index", response_model=IndexResponse)
def index(req: IndexRequest) -> IndexResponse:
    raise NotImplementedError


@app.post("/query", response_model=QueryResponse)
def query(req: QueryRequest) -> QueryResponse:
    raise NotImplementedError
