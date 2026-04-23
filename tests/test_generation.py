"""Generation tests (M2, M5).

Planned cases:
- build_prompt embeds [doc_id:pN] markers for each retrieved chunk.
- extract_citations parses repeated markers and de-duplicates.
- validate_citations flags citations missing informative overlap.
- should_abstain triggers on empty retrieval and on low top score.
- compute_confidence monotonic in retrieval score + citation support.
"""

import pytest

pytest.skip("generation logic lands in M2/M5", allow_module_level=True)
