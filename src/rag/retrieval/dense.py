"""Dense retriever: in-memory cosine similarity, optional Chroma persistence.

TODO (M2):
- index(chunks): embed texts, store matrix or push to Chroma collection.
- query(text, top_k): embed query, return top-k RetrievalResult objects.
"""

from __future__ import annotations

from rag.retrieval.base import Retriever
from rag.retrieval.embeddings import Embedder
from rag.types import Chunk, RetrievalResult
from rag.retrieval.embeddings import Embedder, SentenceTransformerEmbedder 


class DenseRetriever(Retriever):
    name = "dense"

    def __init__(
        self,
        embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2",
        store: str = "memory",
        store_dir: str | None = None,
        embedder: Embedder | None = None,
    ) -> None:
        self.embedding_model = embedding_model
        self.store = store
        self.store_dir = store_dir
        self.embedder = embedder or SentenceTransformerEmbedder(embedding_model)

    def index(self, chunks: list[Chunk]) -> None:
        self.chunks= chunks 
        texts = []
        for chunk in chunks:
            texts.append(chunk.text)

        embeddings = self.embedder.embed(texts)
        self.embeddings = embeddings


        

    def query(self, text: str, top_k: int) -> list[RetrievalResult]:
        query_list = [text] # converting the text into a list because embed() expects a list 
        query_embedding = self.embedder.embed(query_list) 

        scores = []

        query_vector = query_embedding[0]

        for embedding in self.embeddings:
            score = query_vector @ embedding
            scores.append(score)
            
        indexed_scores = []

        
        for i in range(len(scores)):
            indexed_scores.append((i, scores[i]))

        def get_score(item):
            return item [1]
        

        indexed_scores.sort(key=get_score, reverse=True)

        top_results = indexed_scores[:top_k]

        results = []
        rank = 1

        for item in top_results:
            i = item[0]
            score = item[1]

            chunk = self.chunks[i]

            result = RetrievalResult(
                chunk=chunk,
                score=float(score),
                rank=rank,
                retriever=self.name,
        )

        results.append(result)
        rank += 1

        return results

