"""Answer generation: LLM clients, prompts, citation, abstention, confidence."""

from rag.generation.abstention import should_abstain
from rag.generation.citation import extract_citations, validate_citations
from rag.generation.confidence import compute_confidence
from rag.generation.llm_client import LLMClient, build_llm_client
from rag.generation.prompt import build_prompt

__all__ = [
    "LLMClient",
    "build_llm_client",
    "build_prompt",
    "extract_citations",
    "validate_citations",
    "compute_confidence",
    "should_abstain",
]
