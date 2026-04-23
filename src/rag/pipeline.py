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

from pathlib import Path

from rag.config import PipelineConfig
from rag.generation.llm_client import LLMClient
from rag.retrieval import Retriever
from rag.types import Answer, Chunk, Document


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
        raise NotImplementedError

    def add_document_objects(self, documents: list[Document]) -> None:
        raise NotImplementedError

    @property
    def documents(self) -> list[Document]:
        return list(self._documents)

    @property
    def chunks(self) -> list[Chunk]:
        return list(self._chunks)

    def stats(self) -> dict[str, int]:
        raise NotImplementedError

    def answer(self, question: str) -> Answer:
        raise NotImplementedError
