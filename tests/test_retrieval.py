"""Retrieval tests (M2, M4).

Planned cases:
- DenseRetriever returns top_k results in descending score order.
- BM25Retriever ranks exact-match chunks above unrelated ones.
- HybridRetriever (RRF) produces a union of dense+sparse results.
- CrossEncoderReranker pass-through when model unavailable.
"""

import pytest

pytest.skip("retrieval logic lands in M2/M4", allow_module_level=True)
