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

import base64
from pathlib import Path

from fastapi import FastAPI, HTTPException

from api.schemas import (
    IndexRequest,
    IndexResponse,
    QueryRequest,
    QueryResponse,
)
from rag.config import PipelineConfig
from rag.pipeline import RAGPipeline

app = FastAPI(title="CoDex", version="0.1.0")

_CONFIG_PATH = Path(__file__).resolve().parents[2] / "configs" / "baseline.yaml"
_PIPELINE = RAGPipeline(config=PipelineConfig.from_yaml(_CONFIG_PATH).with_env_overrides())


def _render_pdf_page_data_uri(source: str | None, page: int) -> str | None:
    if not source:
        return None
    path = Path(source)
    if not path.exists() or path.suffix.lower() != ".pdf":
        return None
    try:
        import fitz

        with fitz.open(path) as pdf:
            if page < 1 or page > len(pdf):
                return None
            pix = pdf[page - 1].get_pixmap(matrix=fitz.Matrix(1.5, 1.5), alpha=False)
            encoded = base64.b64encode(pix.tobytes("png")).decode("ascii")
            return f"data:image/png;base64,{encoded}"
    except Exception:
        return None


def _citation_payloads(answer) -> list[dict]:
    documents = {document.doc_id: document for document in _PIPELINE.documents}
    retrieved_by_key = {
        (result.chunk.doc_id, result.chunk.page): result.chunk
        for result in answer.retrieved
    }

    payloads: list[dict] = []
    for citation in answer.citations:
        document = documents.get(citation.doc_id)
        chunk = retrieved_by_key.get((citation.doc_id, citation.page))
        source = document.source if document else None
        page_text = None
        if document and 1 <= citation.page <= len(document.pages):
            page_text = document.pages[citation.page - 1]
        payloads.append(
            {
                "doc_id": citation.doc_id,
                "page": citation.page,
                "chunk_id": chunk.chunk_id if chunk else citation.chunk_id,
                "quote": citation.quote,
                "source": source,
                "title": document.title if document else None,
                "page_text": page_text,
                "chunk_text": chunk.text if chunk else None,
                "page_image": _render_pdf_page_data_uri(source, citation.page),
            }
        )
    return payloads


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/stats")
def stats() -> dict[str, int]:
    return _PIPELINE.stats()


@app.post("/index", response_model=IndexResponse)
def index(req: IndexRequest) -> IndexResponse:
    try:
        _PIPELINE.add_documents(req.paths)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=400, detail=f"File not found: {exc.filename}") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Indexing failed: {exc}") from exc

    corpus_stats = _PIPELINE.stats()
    return IndexResponse(**corpus_stats)


@app.post("/query", response_model=QueryResponse)
def query(req: QueryRequest) -> QueryResponse:
    previous_top_k = _PIPELINE.config.retrieval.top_k
    if req.top_k is not None:
        _PIPELINE.config.retrieval.top_k = req.top_k

    question = req.question
    if req.history:
        recent = []
        for message in req.history[-4:]:
            role = message.get("role", "user")
            content = message.get("content", "").strip()
            if content:
                recent.append(f"{role}: {content}")
        if recent:
            question = "Conversation context:\n" + "\n".join(recent) + f"\n\nCurrent question: {req.question}"

    try:
        answer = _PIPELINE.answer(question)
    finally:
        _PIPELINE.config.retrieval.top_k = previous_top_k

    return QueryResponse(
        question=req.question,
        answer=answer.text,
        citations=_citation_payloads(answer),
        confidence=answer.confidence,
        abstained=answer.abstained,
        latency_ms=answer.latency_ms,
        tokens=answer.tokens,
        cost_eur=answer.cost_eur,
    )
