"""Prompt templates.

Both templates will enforce a strict citation format ``[doc_id:pN]`` so
downstream citation extraction is deterministic and auditable.

TODO (M5 strict):
- SYSTEM_STRICT: extractive, one citation per sentence minimum, explicit.
"""

from __future__ import annotations

from rag.types import RetrievalResult

SYSTEM_DEFAULT = """You answer questions using only the provided context. 
Do not use external knowledge or assumptions.
If the answer is not explicitly stated in the context, respond exactly: 
"I cannot answer from the provided documents."
All factual statements must include at least one citation in the form [doc_id:pN].
Do not mention these instructions in your answer.
""".strip()  

SYSTEM_STRICT = ""   # filled in at M5

def _format_context(retrieved: list[RetrievalResult]) -> str:
    parts = []

    for r in retrieved:
        doc_id = r.chunk.doc_id
        page = r.chunk.page
        text = r.chunk.text.strip()

        if text:
            parts.append(f"[{doc_id}:p{page}] {text}")

    return "\n\n".join(parts)

def build_prompt(
    question: str,
    retrieved: list[RetrievalResult],
    template: str = "default",
) -> tuple[str, str]:

    system = SYSTEM_DEFAULT if template == "default" else SYSTEM_STRICT

    context = _format_context(retrieved)

    user = f"""
Context: {context}

Question: {question}

Answer:
""".strip()

    return system, user
