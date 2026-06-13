from __future__ import annotations

import logging
from typing import Any

from rag.types import RetrievalResult

logger = logging.getLogger(__name__)


class CrossEncoderReranker:
    def __init__(self, model_name: str = "BAAI/bge-reranker-base") -> None:
        self.model_name = model_name
        self._model: Any | None = None
        self._disabled = False

    def _load_model(self) -> Any | None:
        if self._disabled:
            return None

        if self._model is not None:
            return self._model

        try:
            from sentence_transformers import CrossEncoder

            self._model = CrossEncoder(self.model_name)
            logger.info("Loaded cross-encoder reranker: %s", self.model_name)
            return self._model

        except Exception as exc:
            logger.warning(
                "Could not load cross-encoder reranker '%s'. Continuing without reranking. Error: %s",
                self.model_name,
                exc,
            )
            self._disabled = True
            return None

    def rerank(
        self,
        query: str,
        hits: list[RetrievalResult],
        top_n: int,
    ) -> list[RetrievalResult]:
        if not hits or top_n <= 0:
            return []

        model = self._load_model()

        if model is None:
            return hits[:top_n]

        pairs = [(query, hit.chunk.text) for hit in hits]

        try:
            scores = model.predict(pairs)
        except Exception as exc:
            logger.warning("Cross-encoder reranking failed: %s", exc)
            return hits[:top_n]

        ranked = sorted(
            zip(hits, scores, strict=False),
            key=lambda item: float(item[1]),
            reverse=True,
        )

        reranked: list[RetrievalResult] = []

        for new_rank, (hit, _rerank_score) in enumerate(ranked[:top_n], start=1):
            reranked.append(
                RetrievalResult(
                    chunk=hit.chunk,
                    score=hit.score,
                    rank=new_rank,
                    retriever=f"{hit.retriever}+rerank",
                )
            )

        return reranked
