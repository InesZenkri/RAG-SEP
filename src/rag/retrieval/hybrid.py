"""Hybrid retriever combining dense and BM25.

Supports two fusion modes (M4):
- ``rrf`` (Reciprocal Rank Fusion, default): robust to score-scale differences.
- ``linear``: min-max normalised scores combined as alpha*dense + (1-alpha)*bm25.
"""

from __future__ import annotations

from rag.retrieval.base import Retriever
from rag.retrieval.bm25 import BM25Retriever
from rag.retrieval.dense import DenseRetriever
from rag.types import Chunk, RetrievalResult


class HybridRetriever(Retriever):
    name = "hybrid"

    def __init__(
        self,
        dense: DenseRetriever,
        sparse: BM25Retriever,
        mode: str = "rrf",
        alpha: float = 0.5,
        rrf_k: int = 60,
    ) -> None:
        self.dense = dense
        self.sparse = sparse
        self.mode = mode
        self.alpha = alpha
        self.rrf_k = rrf_k

    def index(self, chunks: list[Chunk]) -> None:
        self.dense.index(chunks)
        self.sparse.index(chunks)


    def query(self, text: str, top_k: int) -> list[RetrievalResult]:
        
        if top_k <= 0 :
            return []
        
        candidate_k = top_k * 4
        dense_results = self.dense.query( text, candidate_k)
        sparse_results = self.sparse.query( text, candidate_k)


        scores = {}
        results_by_id = {}

        for result in dense_results:
            chunk_id = result.chunk.chunk_id
            rrf_score = 1 / (self.rrf_k + result.rank)
            scores[chunk_id] = scores.get(chunk_id, 0.0) + rrf_score
            results_by_id[chunk_id] = result
        
        for result in sparse_results:
            chunk_id = result.chunk.chunk_id
            rrf_score = 1 / (self.rrf_k + result.rank)
            scores[chunk_id] = scores.get(chunk_id, 0.0) + rrf_score
            results_by_id[chunk_id] = result

        if not scores:
            return []

        sorted_chunk_ids = sorted(
            scores,
            key=lambda chunk_id: scores[chunk_id],
            reverse=True,
        )

        top_chunk_ids = sorted_chunk_ids[:top_k]

        final_results = []

        for rank, chunk_id in enumerate(top_chunk_ids, start=1):
            old_result = results_by_id[chunk_id]

            result = RetrievalResult(
                chunk=old_result.chunk,
                score=scores[chunk_id],
                rank=rank,
                retriever=self.name,
            )

            final_results.append(result)

        return final_results

        



        
        



