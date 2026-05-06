"""BM25 lexical retriever.

TODO (M4):
- Tokenise each chunk and fit a BM25Okapi index (rank_bm25 when available).
- Return top-k RetrievalResults with raw BM25 scores.
- Include a minimal pure-Python BM25 fallback so CI runs without rank_bm25.
"""

from __future__ import annotations

from collections import Counter

from rag.retrieval.base import Retriever
from rag.types import Chunk, RetrievalResult


class BM25Retriever(Retriever):
    name = "bm25"

    def __init__(self, k1: float = 1.5, b: float = 0.75) -> None:
        self.k1 = k1
        self.b = b

        self.chunks = []
        self.tokenized_chunks = []
        self.chunk_lengths = []
        self.term_frequencies = []
        self.avg_chunk_length = 0.0
        


    def index(self, chunks: list[Chunk]) -> None:


        self.chunks = chunks # Storing the original chunks
        self.tokenized_chunks = [] # Creating a list to store each  tokenized chunks
        self.chunk_lengths = [] 
        self.term_frequencies = []
        

        
        
        
        for chunk in chunks:

            # Converting chunk texts into lowercase words and storing them for BM25 retrievel later
            tokens = self.tokenize(chunk.text)
            self.tokenized_chunks.append(tokens) 


            chunk_length = len(tokens)
            self.chunk_lengths.append(chunk_length)

            term_frequency = Counter(tokens)
            self.term_frequencies.append(term_frequency)

            
            
        self.avg_chunk_length = sum(self.chunk_lengths) / len(self.chunk_lengths) if len(self.chunk_lengths) != 0 else 0.0
        

    # Helper method that takes a text and convert it to lowercase words
    def tokenize(self, text : str) -> list[str]:
        return text.lower().split()




    def query(self, text: str, top_k: int) -> list[RetrievalResult]:
        raise NotImplementedError
