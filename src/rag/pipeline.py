"""End-to-end RAG pipeline: ingest -> chunk -> retrieve -> (rerank) -> generate.

This is the orchestrator every milestone plugs into. The constructor accepts
optional pre-built Retriever / LLMClient so tests can inject fakes.

TODO (M2):
- add_documents(paths): parse -> chunk -> index.
- answer(question): retrieve, optional rerank, prompt, generate, extract
  citations, validate, score confidence, decide abstention, return Answer.
- stats(): corpus stats (docs/chunks/pages) for the UI dashboard.
"""

from __future__ import annotations

import os
from pathlib import Path

from rag.cost import estimate_cost_eur
from rag.config import PipelineConfig
from rag.generation.citation import extract_citations
from rag.generation.llm_client import LLMClient
from rag.generation.llm_client import build_llm_client
from rag.generation.prompt import build_prompt
from rag.ingest.parser import parse_document
from rag.retrieval import Retriever
from rag.retrieval.bm25 import BM25Retriever
from rag.chunking.recursive import chunk_document
from rag.logging_utils import timed
from rag.types import Answer, Chunk, Document, RetrievalResult


class RAGPipeline:
    def __init__(
        self,
        config: PipelineConfig,
        retriever: Retriever | None = None,
        llm: LLMClient | None = None,
    ) -> None:
        self.config = config
        self.retriever = retriever
        self.llm = llm
        self._documents: list[Document] = []
        self._chunks: list[Chunk] = []

    def add_documents(self, paths: list[str | Path]) -> None:
        documents = [parse_document(path, config=self.config.ingest) for path in paths]
        self.add_document_objects(documents)

    def add_document_objects(self, documents: list[Document]) -> None:
        new_chunks: list[Chunk] = []
        for document in documents:
            new_chunks.extend(chunk_document(document, config=self.config.chunking))

        self._documents.extend(documents)
        self._chunks.extend(new_chunks)

        if not self._chunks:
            return
        if self.retriever is None:
            self.retriever = BM25Retriever()
        self.retriever.index(self._chunks)

    @property
    def documents(self) -> list[Document]:
        return list(self._documents)

    @property
    def chunks(self) -> list[Chunk]:
        return list(self._chunks)

    def stats(self) -> dict[str, int]:
        return {
            "documents": len(self._documents),
            "chunks": len(self._chunks),
            "pages": sum(document.num_pages for document in self._documents),
        }

    def answer(self, question: str) -> Answer:
        answer = Answer(question=question, text="")

        if self.retriever is None or not self._chunks:
            answer.text = "I cannot answer from the provided documents."
            answer.abstained = True
            answer.confidence = 0.0
            return answer

        top_k = self.config.retrieval.top_k
        with timed(answer.latency_ms, "retrieval"):
            retrieved = self.retriever.query(question, top_k=top_k)
            if self._is_broad_document_question(question):
                retrieved = self._add_first_page_context(retrieved, top_k)
        answer.retrieved = retrieved

        if not retrieved:
            answer.text = "I cannot answer from the provided documents."
            answer.abstained = True
            answer.confidence = 0.0
            return answer

        system, user = build_prompt(
            question,
            retrieved,
            template=self.config.generation.prompt_template,
        )

        if self.llm is None:
            provider_override = os.getenv("RAG_GENERATION_PROVIDER")
            provider = provider_override or self.config.generation.provider
            if provider_override is None and provider == "echo" and os.getenv("GEMINI_API_KEY"):
                provider = "gemini"
            self.llm = build_llm_client(
                provider=provider,
                model=self.config.generation.model,
                cache_dir=None,
            )

        with timed(answer.latency_ms, "generation"):
            response = self.llm.complete(
                system,
                user,
                temperature=self.config.generation.temperature,
                max_tokens=self.config.generation.max_tokens,
            )

        answer.text = response.text.strip()
        answer.citations = extract_citations(answer.text)
        answer.tokens = {
            "input": response.input_tokens,
            "output": response.output_tokens,
        }
        answer.cost_eur = estimate_cost_eur(
            response.input_tokens,
            response.output_tokens,
            self.config.cost.eur_per_1k_input,
            self.config.cost.eur_per_1k_output,
        )
        answer.abstained = answer.text == "I cannot answer from the provided documents."
        answer.confidence = 0.0 if answer.abstained else min(1.0, max(0.1, retrieved[0].score))
        answer.trace = {
            "provider": response.provider,
            "model": response.model,
            "cached": response.cached,
            "finish_reason": response.finish_reason,
            "retrieved": len(retrieved),
        }
        return answer

    def _is_broad_document_question(self, question: str) -> bool:
        terms = question.lower()
        return any(
            marker in terms
            for marker in (
                "who",
                "author",
                "authors",
                "working on",
                "worked on",
                "team",
                "member",
                "members",
                "about",
                "title",
            )
        )

    def _add_first_page_context(
        self, retrieved: list[RetrievalResult], top_k: int
    ) -> list[RetrievalResult]:
        seen = {result.chunk.chunk_id for result in retrieved}
        first_page_chunks = [
            chunk
            for document in self._documents
            for chunk in self._chunks
            if chunk.doc_id == document.doc_id and chunk.page == 1 and chunk.chunk_id not in seen
        ]
        merged = list(retrieved)
        for chunk in first_page_chunks:
            if len(merged) >= top_k:
                merged = merged[: max(0, top_k - 1)]
            merged.append(
                RetrievalResult(
                    chunk=chunk,
                    score=0.01,
                    rank=len(merged) + 1,
                    retriever="first_page_fallback",
                )
            )
            break
        return merged
