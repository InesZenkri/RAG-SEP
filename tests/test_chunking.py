"""Chunking tests (M2).

Planned cases:
- recursive_split respects chunk_size and chunk_overlap bounds.
- chunk_document preserves doc_id and assigns sensible page numbers.
- chunk_ids are unique within a document.
"""

import pytest

pytest.skip("chunking logic lands in M2", allow_module_level=True)
