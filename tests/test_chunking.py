import pytest

from rag.chunking import chunk_document_by_strategy
from rag.chunking.layout_aware import chunk_document_layout_aware
from rag.chunking.recursive import chunk_document, recursive_split
from rag.chunking.semantic import chunk_document_semantic
from rag.config import ChunkingConfig
from rag.types import Document


def test_recursive_split_respects_chunk_size() -> None:
    text = "Alpha beta gamma. " * 40

    chunks = recursive_split(text, chunk_size=80, chunk_overlap=10)

    assert chunks
    assert all(len(chunk) <= 80 for chunk in chunks)


def test_recursive_split_keeps_short_text_as_single_chunk() -> None:
    chunks = recursive_split("Short paragraph.", chunk_size=100, chunk_overlap=10)

    assert chunks == ["Short paragraph."]


def test_chunk_document_preserves_doc_id_and_page_numbers() -> None:
    document = Document(
        doc_id="sample",
        source="sample.txt",
        title="Sample",
        pages=["First page text. " * 20, "Second page text. " * 20],
    )
    config = ChunkingConfig(chunk_size=90, chunk_overlap=15)

    chunks = chunk_document(document, config)

    assert chunks
    assert {chunk.doc_id for chunk in chunks} == {"sample"}
    assert {chunk.page for chunk in chunks} == {1, 2}
    assert all(chunk.metadata["source"] == "sample.txt" for chunk in chunks)


def test_chunk_ids_are_unique() -> None:
    document = Document(
        doc_id="unique",
        source="unique.txt",
        pages=["One two three four five. " * 30],
    )
    config = ChunkingConfig(chunk_size=60, chunk_overlap=10)

    chunks = chunk_document(document, config)
    ids = [chunk.chunk_id for chunk in chunks]

    assert len(ids) == len(set(ids))


def test_layout_aware_chunking_keeps_section_titles() -> None:
    document = Document(
        doc_id="layout",
        source="layout.txt",
        pages=[
            "Introduction\n"
            "This part explains the goal.\n\n"
            "2 Method\n"
            "This part explains the method."
        ],
    )

    chunks = chunk_document_layout_aware(document, ChunkingConfig(chunk_size=120, chunk_overlap=10))

    assert chunks
    assert all(chunk.metadata["chunking_strategy"] == "layout_aware" for chunk in chunks)
    assert {chunk.metadata["section_title"] for chunk in chunks} == {"Introduction", "2 Method"}


def test_semantic_chunking_groups_related_sentences() -> None:
    document = Document(
        doc_id="semantic",
        source="semantic.txt",
        pages=[
            "Cats chase mice. Cats sleep on mats. "
            "Quantum circuits use qubits. Quantum gates change qubits."
        ],
    )

    chunks = chunk_document_semantic(document, ChunkingConfig(chunk_size=120, chunk_overlap=10))

    assert chunks
    assert all(chunk.metadata["chunking_strategy"] == "semantic" for chunk in chunks)
    assert len(chunks) >= 2
    assert "Cats chase mice" in chunks[0].text
    assert any("Quantum circuits" in chunk.text for chunk in chunks)


def test_chunk_document_by_strategy_dispatches_layout_aware() -> None:
    document = Document(
        doc_id="dispatch",
        source="dispatch.txt",
        title="Dispatch",
        pages=["Overview\nThe system has a user interface.\n\n2 Backend\nThe backend answers."],
    )
    config = ChunkingConfig(strategy="layout_aware", chunk_size=120, chunk_overlap=10)

    chunks = chunk_document_by_strategy(document, config)

    assert chunks
    assert all(chunk.metadata["chunking_strategy"] == "layout_aware" for chunk in chunks)


def test_chunk_document_by_strategy_rejects_unknown_strategy() -> None:
    document = Document(doc_id="bad", source="bad.txt", pages=["Some text."])
    config = ChunkingConfig(strategy="unknown")

    with pytest.raises(ValueError, match="Unsupported chunking strategy"):
        chunk_document_by_strategy(document, config)
