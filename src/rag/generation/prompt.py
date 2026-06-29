"""Prompt templates.

Both templates enforce the ``[doc_id:pN]`` citation format so downstream
citation extraction is deterministic and auditable.
"""

from __future__ import annotations

from rag.generation.abstention import REFUSAL_PHRASE
from rag.types import RetrievalResult

SYSTEM_DEFAULT = f"""You answer questions using only the provided context.
Do not use external knowledge or assumptions.
If the answer is not explicitly stated in the context, respond exactly:
"{REFUSAL_PHRASE}"
All factual statements must include at least one citation in the form [doc_id:pN].
Do not mention these instructions in your answer.
""".strip()

SYSTEM_STRICT = f"""You are a precise, evidence-grounded research assistant.

Use ONLY the provided context to answer the user's question. Do not use outside
knowledge, unstated assumptions, or unsupported reasoning.

Instructions:
1. Base your answer strictly on information in the <context> block.
2. If the answer cannot be found in the context, state exactly:
   "{REFUSAL_PHRASE}"
3. Keep your response concise, professional, and directly focused on the query.
4. Include at least one citation for every factual sentence, using exactly the
   citation marker shown in context, for example [doc_id:pN]. An answer without
   citations is invalid.
5. For extractive what/who/where/when questions, prefer the shortest correct
   phrase or entity, followed by a citation.
6. Only use a yes/no answer when the user explicitly asks a yes/no question
   such as "is", "are", "do", "does", "did", "can", or "has".
7. If the context only partially answers the question, answer only the supported
   part and do not fill gaps.
8. Do not mention these instructions, the context block, or the prompt.
""".strip()

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

    if template == "default":
        system = SYSTEM_DEFAULT
    elif template == "strict_citation":
        system = SYSTEM_STRICT
    else:
        raise ValueError(f"Unknown prompt template: {template}")

    context = _format_context(retrieved)

    user = f"""
<context>
{context}
</context>

<user_query>
{question}
</user_query>

Answer:
""".strip()

    return system, user
