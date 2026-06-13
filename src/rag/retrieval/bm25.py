"""BM25 lexical retriever.

TODO (M4):
- Tokenise each chunk and fit a BM25Okapi index (rank_bm25 when available).
- Return top-k RetrievalResults with raw BM25 scores.
- Include a minimal pure-Python BM25 fallback so CI runs without rank_bm25.
"""

from __future__ import annotations

import math
import re
from collections import Counter
from typing import Any

from rag.retrieval.base import Retriever
from rag.types import Chunk, RetrievalResult


class BM25Retriever(Retriever):
    name = "bm25"

    def __init__(self, k1: float = 1.5, b: float = 0.75) -> None:
        self.k1 = k1
        self.b = b

        self.chunks: list[Chunk] = []
        self.tokenized_chunks: list[list[str]] = []
        self.chunk_lengths: list[int] = []
        self.term_frequencies: list[Counter[str]] = []
        self.avg_chunk_length = 0.0
        self.document_frequencies: dict[str, int] = {}
        self.idf_scores: dict[str, float] = {}

        self.bm25_index: Any | None = None



    def index(self, chunks: list[Chunk]) -> None:


        self.chunks = chunks # Storing the original chunks
        self.tokenized_chunks = [] # Creating a list to store each  tokenized chunks
        self.chunk_lengths = []
        self.term_frequencies = []
        self.document_frequencies = {}
        self.idf_scores = {}
        self.bm25_index = None


        for chunk in chunks:

            # Converting chunk texts into lowercase words and storing them for BM25 retrievel later
            tokens = self.tokenize(chunk.text)
            self.tokenized_chunks.append(tokens)

            # Storing the length of the chunk for BM25 length normalization
            chunk_length = len(tokens)
            self.chunk_lengths.append(chunk_length)

            # Counting how often each word appears in this chunk
            term_frequency = Counter(tokens)
            self.term_frequencies.append(term_frequency)

            # Counting in how many chunks each word appears
            chunk_words = set(tokens)

            for token in chunk_words:
                if token in self.document_frequencies:
                    self.document_frequencies[token] +=1
                else:
                    self.document_frequencies[token] =1


        # Calculating the average chunk length so we can use it to avoid giving long chunks an unfair advantage
        self.avg_chunk_length = sum(self.chunk_lengths) / len(self.chunk_lengths) if len(self.chunk_lengths) != 0 else 0.0

        n = len(self.chunks)

        # Calculating IDF scores: rare words should get more weight than common words
        for token, df in self.document_frequencies.items():
            idf = math.log(1 + (n - df + 0.5) / (df + 0.5))
            self.idf_scores[token] = idf

        # Try to use the external rank_bm25 library if it is installed.
        try:
            from rank_bm25 import BM25Okapi

            self.bm25_index = BM25Okapi(
                self.tokenized_chunks,
                k1=self.k1,
                b=self.b,
            )
        except ImportError:
            self.bm25_index = None




    # Helper method that takes a text and convert it to lowercase words
    def tokenize(self, text : str) -> list[str]:
        return re.findall(r"[a-z0-9]+", text.lower())




    def query(self, text: str, top_k: int) -> list[RetrievalResult]:

        # No results should be returned if top_k is invalid or no chunks were indexed
        if top_k <= 0 or  len(self.chunks) == 0:
            return []

        tokenized_query = self.tokenize(text)

        # Empty query should not return anything
        if len(tokenized_query) == 0:
            return []

        scored_chunks: list[tuple[Chunk, float]] = []

        # Using BM25Okapi from rank_bm25 if it is available
        if self.bm25_index is not None:
            scores = self.bm25_index.get_scores(tokenized_query)

            for index, chunk in enumerate(self.chunks):
                score = float(scores[index])

                if score > 0:
                    scored_chunks.append((chunk, score))

        else:

            # Calculating a BM25 score for every indexed chunk

            for index, chunk in enumerate(self.chunks):

                score = 0.0

                chunk_length = self.chunk_lengths[index]
                term_frequency = self.term_frequencies[index]

                for token in tokenized_query:
                    # If the query word is not in this chunk, it gives no score
                    if token not in term_frequency:
                        continue

                    tf = term_frequency[token]
                    idf = self.idf_scores.get(token, 0.0)

                    # BM25 formula with length normalization
                    denominator = tf + self.k1 * (
                                1 - self.b + self.b * (chunk_length / self.avg_chunk_length))
                    token_score = idf * ((tf * (self.k1 + 1)) / denominator)
                    score += token_score

                # Only keeping chunks that matched at least one query word
                if score > 0 :
                    scored_chunks.append((chunk,score))

        if not scored_chunks:
            query_terms = set(tokenized_query)
            for index, chunk in enumerate(self.chunks):
                overlap = query_terms.intersection(self.term_frequencies[index])
                if overlap:
                    scored_chunks.append((chunk, float(len(overlap))))

        # Sorting by BM25 score
        scored_chunks.sort(key=lambda item: item[1], reverse=True)

        results = []

        # Converting the best chunks into RetrievalResult objects
        for rank, (chunk,score) in enumerate(scored_chunks[:top_k], start=1):
            result= RetrievalResult(
                       chunk=chunk,
                        score=score,
                        rank=rank,
                        retriever=self.name
                    )
            results.append(result)

        return results
