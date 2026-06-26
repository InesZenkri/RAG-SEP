import sys
import types

from rag.config import PipelineConfig
from rag.types import Chunk, Document

sys.modules.setdefault("dotenv", types.SimpleNamespace(load_dotenv=lambda: None))
sys.modules.setdefault("requests", types.SimpleNamespace())
retrieval_module = types.ModuleType("rag.retrieval")
retrieval_module.Retriever = object
retrieval_factory_module = types.ModuleType("rag.retrieval.factory")
retrieval_factory_module.build_retriever = lambda config: None
rerank_module = types.ModuleType("rag.retrieval.rerank")
rerank_module.CrossEncoderReranker = lambda model: None
sys.modules.setdefault("rag.retrieval", retrieval_module)
sys.modules.setdefault("rag.retrieval.factory", retrieval_factory_module)
sys.modules.setdefault("rag.retrieval.rerank", rerank_module)


class RecordingRetriever:
    def __init__(self) -> None:
        self.indexed: list[Chunk] = []

    def index(self, chunks: list[Chunk]) -> None:
        self.indexed = chunks

    def query(self, question: str, top_k: int):
        return []


def test_pipeline_uses_configured_chunking_strategy() -> None:
    from rag.pipeline import RAGPipeline

    config = PipelineConfig.from_dict(
        {
            "chunking": {
                "strategy": "layout_aware",
                "chunk_size": 120,
                "chunk_overlap": 10,
            }
        }
    )
    retriever = RecordingRetriever()
    pipeline = RAGPipeline(config=config, retriever=retriever)
    document = Document(
        doc_id="pipeline",
        source="pipeline.txt",
        title="Pipeline",
        pages=["Introduction\nThe UI sends requests.\n\n2 Backend\nThe backend processes them."],
    )

    pipeline.add_document_objects([document])

    assert retriever.indexed
    assert all(chunk.metadata["chunking_strategy"] == "layout_aware" for chunk in retriever.indexed)
