from eval.dataset import EvalItem
from eval.metrics.grounding import citation_precision, citation_recall
from eval.run import _compute_retrieval, _gold_retrieval_keys
from rag.generation.citation import extract_citations
from rag.types import Answer, Chunk, Citation, RetrievalResult


def make_result(doc_id: str, page: int, text: str) -> RetrievalResult:
    return RetrievalResult(
        chunk=Chunk(
            chunk_id=f"{doc_id}:p{page}:c1",
            doc_id=doc_id,
            text=text,
            page=page,
        ),
        score=1.0,
        rank=1,
        retriever="test",
    )


def test_gold_retrieval_keys_match_ingested_text_file_doc_ids():
    item = EvalItem(
        id="q1",
        question="What are the products of photosynthesis?",
        answer="glucose and oxygen",
        doc_sources=["photosynthesis.txt"],
        pages=[1],
    )

    assert _gold_retrieval_keys(item) == {"photosynthesis:p1"}


def test_retrieval_metrics_count_stem_matched_sample_sources():
    item = EvalItem(
        id="q1",
        question="What are the products of photosynthesis?",
        answer="glucose and oxygen",
        doc_sources=["photosynthesis.txt"],
        pages=[1],
    )
    answer = Answer(
        question=item.question,
        text="glucose and oxygen [photosynthesis:p1]",
        retrieved=[
            make_result(
                "photosynthesis",
                1,
                "Photosynthesis produces glucose and oxygen.",
            )
        ],
    )

    metrics = _compute_retrieval([(item, answer)])

    assert metrics == {
        "recall@5": 1.0,
        "mrr": 1.0,
        "ndcg@5": 1.0,
        "hit@5": 1.0,
    }


def test_citation_precision_accepts_doc_page_citations_without_chunk_id_or_quote():
    answer = Answer(
        question="What are the products of photosynthesis?",
        text="Photosynthesis produces glucose and oxygen. [photosynthesis:p1]",
        citations=[Citation(doc_id="photosynthesis", page=1)],
        retrieved=[
            make_result(
                "photosynthesis",
                1,
                "Photosynthesis produces glucose and oxygen from carbon dioxide and water.",
            )
        ],
    )

    assert citation_precision(answer) == 1.0


def test_angle_wrapped_citations_parse_to_plain_doc_page_keys():
    citations = extract_citations("Self-attention [<transformers:p1>]")

    assert [citation.key() for citation in citations] == ["transformers:p1"]


def test_arxiv_style_citations_keep_dotted_doc_ids():
    citations = extract_citations("Impedance estimation is challenging [2410.14077v2:p1].")

    assert [citation.key() for citation in citations] == ["2410.14077v2:p1"]


def test_citation_precision_accepts_angle_wrapped_citation_markers():
    answer = Answer(
        question="What technique replaces recurrence in Transformers?",
        text="Self-attention [<transformers:p1>]",
        citations=[Citation(doc_id="transformers", page=1)],
        retrieved=[
            make_result(
                "transformers",
                1,
                "Transformers replace recurrence with self-attention.",
            )
        ],
    )

    assert citation_precision(answer) == 1.0


def test_citation_recall_keeps_citation_only_fragments_with_previous_claim():
    answer = Answer(
        question="Who introduced the Transformer architecture?",
        text="Vaswani et al. [transformers:p1]",
        citations=[Citation(doc_id="transformers", page=1)],
    )

    assert citation_recall(answer) == 1.0
