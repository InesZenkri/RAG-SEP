"""Prompt templates.

Both templates will enforce a strict citation format ``[doc_id:pN]`` so
downstream citation extraction is deterministic and auditable.

TODO (M2 baseline, M5 strict):
- build_prompt(question, retrieved, template): return (system, user).
- SYSTEM_DEFAULT: friendly, cite-after-each-claim.
- SYSTEM_STRICT: extractive, one citation per sentence minimum, explicit
  "cannot answer" phrase when context is insufficient.
"""

from __future__ import annotations

from rag.types import RetrievalResult

SYSTEM_DEFAULT = ""  # filled in at M2
SYSTEM_STRICT = ""   # filled in at M5


def build_prompt(
    question: str,
    retrieved: list[RetrievalResult],
    template: str = "default",
) -> tuple[str, str]:
    raise NotImplementedError
