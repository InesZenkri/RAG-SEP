"""End-to-end RAG pipeline: ingest -> chunk -> retrieve -> (rerank) -> generate.

This is the orchestrator every milestone plugs into. The constructor accepts
optional pre-built Retriever / LLMClient so tests can inject fakes.
"""

from __future__ import annotations

import os
from collections.abc import Sequence
from pathlib import Path

from rag.chunking import chunk_document_by_strategy
from rag.config import PipelineConfig
from rag.cost import estimate_cost_eur
from rag.generation.abstention import REFUSAL_PHRASE, AbstentionDecision, should_abstain
from rag.generation.citation import extract_citations, validate_citations
from rag.generation.confidence import compute_confidence
from rag.generation.llm_client import LLMClient, build_llm_client
from rag.generation.prompt import build_prompt
from rag.ingest.parser import parse_document
from rag.logging_utils import timed
from rag.retrieval import Retriever
from rag.retrieval.factory import build_retriever
from rag.retrieval.rerank import CrossEncoderReranker
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
        self.reranker = (
            CrossEncoderReranker(config.retrieval.reranker_model)
            if config.retrieval.rerank
            else None
        )

    def add_documents(self, paths: Sequence[str | Path]) -> None:
        documents = [parse_document(path, config=self.config.ingest) for path in paths]
        self.add_document_objects(documents)

    def add_document_objects(self, documents: list[Document]) -> None:
        new_chunks: list[Chunk] = []
        for document in documents:
            new_chunks.extend(chunk_document_by_strategy(document, config=self.config.chunking))

        self._documents.extend(documents)
        self._chunks.extend(new_chunks)

        if not self._chunks:
            return
        if self.retriever is None:
            self.retriever = build_retriever(self.config.retrieval)
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
            return self._abstain(answer, should_abstain([], None, self.config.abstention))

        top_k = self.config.retrieval.top_k
        candidate_k = max(top_k, self.config.retrieval.rerank_top_n)

        with timed(answer.latency_ms, "retrieval"):
            retrieved = self.retriever.query(question, top_k=candidate_k)

            if self._is_broad_document_question(question):
                retrieved = self._add_first_page_context(retrieved, candidate_k)

        with timed(answer.latency_ms, "rerank"):
            if self.reranker is not None:
                retrieved = self.reranker.rerank(question, retrieved, top_n=top_k)
            else:
                retrieved = retrieved[:top_k]

        answer.retrieved = retrieved

        pre_decision = should_abstain(retrieved, None, self.config.abstention)
        if pre_decision.abstain:
            return self._abstain(answer, pre_decision)

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
                cache_dir=self.config.cache_dir if self.config.cache_enabled else None,
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
        citation_supports = validate_citations(answer.text, retrieved)
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

        post_decision = should_abstain(
            retrieved,
            answer.text,
            self.config.abstention,
            citation_supports=citation_supports,
        )
        if post_decision.abstain:
            return self._abstain(
                answer,
                post_decision,
                trace={
                    "provider": response.provider,
                    "model": response.model,
                    "cached": response.cached,
                    "finish_reason": response.finish_reason,
                    "retrieved": len(retrieved),
                    "citation_support": self._citation_support_trace(citation_supports),
                },
            )

        answer.abstained = False
        answer.confidence = compute_confidence(retrieved, citation_supports)
        answer.trace = {
            "provider": response.provider,
            "model": response.model,
            "cached": response.cached,
            "finish_reason": response.finish_reason,
            "retrieved": len(retrieved),
            "abstention": {
                "reason": post_decision.reason,
                "top_score": post_decision.top_score,
            },
            "citation_support": self._citation_support_trace(citation_supports),
        }
        return answer

    def _abstain(
        self,
        answer: Answer,
        decision: AbstentionDecision,
        trace: dict | None = None,
    ) -> Answer:
        answer.text = REFUSAL_PHRASE
        answer.abstained = True
        answer.confidence = 0.0
        answer.trace = trace or {
            "abstention": {
                "reason": decision.reason,
                "top_score": decision.top_score,
            },
        }
        if "abstention" not in answer.trace:
            answer.trace["abstention"] = {
                "reason": decision.reason,
                "top_score": decision.top_score,
            }
        return answer

    @staticmethod
    def _citation_support_trace(citation_supports) -> list[dict]:
        return [
            {
                "doc_id": support.citation.doc_id,
                "page": support.citation.page,
                "supported": support.supported,
                "overlap": support.overlap,
            }
            for support in citation_supports
        ]

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
