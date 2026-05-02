"""Token-to-euro cost helpers (efficiency metric)."""

from __future__ import annotations


def estimate_cost_eur(
    input_tokens: int,
    output_tokens: int,
    eur_per_1k_input: float,
    eur_per_1k_output: float,
) -> float:
    """Convert token counts to an estimated cost in euros.

    Args:
        input_tokens: Number of prompt tokens consumed.
        output_tokens: Number of completion tokens generated.
        eur_per_1k_input: Provider's input price per 1 000 tokens (EUR).
        eur_per_1k_output: Provider's output price per 1 000 tokens (EUR).

    Returns:
        Estimated cost in euros (>= 0.0).
    """
    # rates are per 1 000 tokens (see https://ai.google.dev/gemini-api/docs/tokens)
    return (input_tokens * eur_per_1k_input + output_tokens * eur_per_1k_output) / 1_000.0


def approx_token_count(text: str) -> int:
    """Estimate token count without a tokenizer (~4 chars per token).

    Used as a fallback when the LLM provider does not return usage statistics
    (e.g. Gemini free tier in streaming mode).  Accuracy is ±20 % for English;
    good enough for cost budgeting and the efficiency metric.

    Args:
        text: Raw text whose tokens you want to count.

    Returns:
        Estimated token count (minimum 1 to avoid division-by-zero downstream).
    """
    # ~4 chars per token for Gemini (https://ai.google.dev/gemini-api/docs/tokens)
    return max(1, len(text) // 4)
