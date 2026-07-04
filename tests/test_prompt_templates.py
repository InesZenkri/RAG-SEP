from __future__ import annotations

import pytest

from rag.generation.abstention import REFUSAL_PHRASE
from rag.generation.prompt import build_prompt
from rag.types import Chunk, RetrievalResult


def _result() -> RetrievalResult:
    chunk = Chunk(
        chunk_id="chunk-1",
        doc_id="doc-a",
        page=3,
        text="The answer is supported here.",
    )
    return RetrievalResult(chunk=chunk, score=0.9, rank=1, retriever="test")


def test_strict_prompt_has_role_context_query_and_citation_rules() -> None:
    system, user = build_prompt(
        "What is supported?",
        [_result()],
        template="strict_citation",
    )

    assert "You are a precise, evidence-grounded research assistant." in system
    assert "Use ONLY the provided context" in system
    assert "citation marker shown in context" in system
    assert "An answer without\n   citations is invalid." in system
    assert "prefer the shortest correct\n   phrase or entity" in system
    assert REFUSAL_PHRASE in system
    assert "<context>" in user
    assert "[doc-a:p3] The answer is supported here." in user
    assert "<user_query>\nWhat is supported?\n</user_query>" in user


def test_unknown_prompt_template_fails_fast() -> None:
    with pytest.raises(ValueError, match="Unknown prompt template"):
        build_prompt("Question?", [_result()], template="typo")
