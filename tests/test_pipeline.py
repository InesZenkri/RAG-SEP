"""End-to-end pipeline tests (M2).

Planned cases:
- add_documents ingests the sample corpus and stats() reflects it.
- answer() on a known-good question returns a non-empty answer with >= 1
  citation pointing to the expected source.
- answer() on an unanswerable question abstains.
- Echo LLM works without any API key (CI default).
"""

import pytest

pytest.skip("pipeline logic lands in M2", allow_module_level=True)
