from eval.dataset import EvalItem
from eval.run import _compute_retrieval, _gold_retrieval_keys
from eval.metrics.grounding import citation_precision
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

