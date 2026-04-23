"""Token-to-euro cost helpers (efficiency metric).

TODO (M2):
- estimate_cost_eur(input_tokens, output_tokens, eur_per_1k_input, eur_per_1k_output)
- approx_token_count(text): rough ~4 chars/token proxy for providers that
  don't return usage.
"""

from __future__ import annotations


def estimate_cost_eur(
    input_tokens: int,
    output_tokens: int,
    eur_per_1k_input: float,
    eur_per_1k_output: float,
) -> float:
    raise NotImplementedError


def approx_token_count(text: str) -> int:
    raise NotImplementedError
