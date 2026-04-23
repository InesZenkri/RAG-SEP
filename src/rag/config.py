"""Typed pipeline configuration, YAML-loadable."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class IngestConfig:
    parser: str = "pymupdf"  # pymupdf | pdfplumber | auto
    strip_headers_footers: bool = False
    extract_tables: bool = False
    ocr: bool = False
    ocr_language: str = "eng"


@dataclass
class ChunkingConfig:
    strategy: str = "recursive"  # recursive | layout_aware | semantic
    chunk_size: int = 800
    chunk_overlap: int = 120
    separators: list[str] = field(default_factory=lambda: ["\n\n", "\n", ". ", " "])


@dataclass
class RetrievalConfig:
    mode: str = "dense"  # dense | bm25 | hybrid
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    top_k: int = 5
    hybrid_alpha: float = 0.5  # weight for dense in linear fusion
    rrf_k: int = 60  # reciprocal-rank fusion constant
    rerank: bool = False
    reranker_model: str = "BAAI/bge-reranker-base"
    rerank_top_n: int = 20
    store: str = "memory"  # memory | chroma
    store_dir: str | None = None


@dataclass
class GenerationConfig:
    provider: str = "echo"  # echo | groq | huggingface
    model: str = "llama-3.1-8b-instant"
    temperature: float = 0.1
    max_tokens: int = 512
    prompt_template: str = "default"  # default | strict_citation
    citation_style: str = "bracket"  # bracket | footnote


@dataclass
class AbstentionConfig:
    enabled: bool = True
    min_retrieval_score: float = 0.15
    min_citations: int = 1
    contradiction_check: bool = False


@dataclass
class CostConfig:
    eur_per_1k_input: float = 0.0
    eur_per_1k_output: float = 0.0


@dataclass
class PipelineConfig:
    name: str = "baseline"
    ingest: IngestConfig = field(default_factory=IngestConfig)
    chunking: ChunkingConfig = field(default_factory=ChunkingConfig)
    retrieval: RetrievalConfig = field(default_factory=RetrievalConfig)
    generation: GenerationConfig = field(default_factory=GenerationConfig)
    abstention: AbstentionConfig = field(default_factory=AbstentionConfig)
    cost: CostConfig = field(default_factory=CostConfig)
    cache_dir: str = "./.llm_cache"

    @classmethod
    def from_yaml(cls, path: str | Path) -> PipelineConfig:
        data = yaml.safe_load(Path(path).read_text()) or {}
        return cls.from_dict(data)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PipelineConfig:
        def _merge(kls, section):
            defaults = kls()
            if not section:
                return defaults
            for k, v in section.items():
                if hasattr(defaults, k):
                    setattr(defaults, k, v)
            return defaults

        return cls(
            name=data.get("name", "baseline"),
            ingest=_merge(IngestConfig, data.get("ingest", {})),
            chunking=_merge(ChunkingConfig, data.get("chunking", {})),
            retrieval=_merge(RetrievalConfig, data.get("retrieval", {})),
            generation=_merge(GenerationConfig, data.get("generation", {})),
            abstention=_merge(AbstentionConfig, data.get("abstention", {})),
            cost=_merge(CostConfig, data.get("cost", {})),
            cache_dir=data.get("cache_dir", "./.llm_cache"),
        )

    def with_env_overrides(self) -> PipelineConfig:
        """Apply environment variable overrides (e.g. from .env)."""
        if os.getenv("RAG_LLM_CACHE_DIR"):
            self.cache_dir = os.environ["RAG_LLM_CACHE_DIR"]
        if os.getenv("RAG_COST_PER_1K_INPUT"):
            self.cost.eur_per_1k_input = float(os.environ["RAG_COST_PER_1K_INPUT"])
        if os.getenv("RAG_COST_PER_1K_OUTPUT"):
            self.cost.eur_per_1k_output = float(os.environ["RAG_COST_PER_1K_OUTPUT"])
        if os.getenv("GROQ_MODEL") and self.generation.provider == "groq":
            self.generation.model = os.environ["GROQ_MODEL"]
        return self
