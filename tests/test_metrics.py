"""Metric unit tests (M1).

Planned cases:
- recall_at_k, mrr, ndcg_at_k on synthetic gold/retrieved lists.
- exact_match and token_f1 with SQuAD-style normalisation.
- citation_precision / citation_recall on crafted Answer objects.
- false_refusal_rate / false_answer_rate sanity cases.
- summarise_efficiency averages latency and sums cost correctly.
"""

import pytest

pytest.skip("metrics logic lands in M1", allow_module_level=True)
