from eval.dataset import EvalItem
from eval.metrics.robustness import robustness_report, slice_by
from rag.types import Answer, Chunk, Citation, RetrievalResult


def _hit(doc_id: str, text: str) -> RetrievalResult:
    return RetrievalResult(
        chunk=Chunk(chunk_id=f"{doc_id}:p1:c1", doc_id=doc_id, text=text, page=1),
        score=1.0,
        rank=1,
        retriever="test",
    )


def test_slice_by_groups_type_and_metadata_flags() -> None:
    answer = Answer(question="q", text="a")
    pairs = [
        (
            EvalItem(
                id="a",
                question="q",
                answer="a",
                type="extractive",
                metadata={"tabular": True, "difficulty": "hard"},
            ),
            answer,
        ),
        (
            EvalItem(
                id="b",
                question="q",
                type="unanswerable",
                metadata={"contradiction": True, "difficulty": "hard"},
            ),
            answer,
        ),
    ]

    assert set(slice_by(pairs, "type")) == {"type:extractive", "type:unanswerable"}
    assert len(slice_by(pairs, "tabular")["tabular"]) == 1
    assert len(slice_by(pairs, "difficulty")["difficulty:hard"]) == 2


def test_robustness_report_computes_slice_metrics() -> None:
    answerable = EvalItem(
        id="answerable",
        question="What does photosynthesis produce?",
        answer="glucose and oxygen",
        type="extractive",
        metadata={"long_doc": True},
    )
    unanswerable = EvalItem(
        id="unanswerable",
        question="What color is the hidden figure?",
        type="unanswerable",
        metadata={"contradiction": True},
    )
    good_answer = Answer(
        question=answerable.question,
        text="Photosynthesis produces glucose and oxygen. [photosynthesis:p1]",
        citations=[Citation(doc_id="photosynthesis", page=1)],
        retrieved=[
            _hit(
                "photosynthesis",
                "Photosynthesis produces glucose and oxygen from carbon dioxide and water.",
            )
        ],
        confidence=0.9,
    )
    refused = Answer(
        question=unanswerable.question,
        text="I cannot answer from the provided documents.",
        abstained=True,
        confidence=0.0,
    )

    report = robustness_report([(answerable, good_answer), (unanswerable, refused)])

    assert report["all"]["count"] == 2.0
    assert report["all"]["false_answer_rate"] == 0.0
    assert report["all"]["false_refusal_rate"] == 0.0
    assert report["long_doc"]["answer_token_f1"] > 0.6
    assert report["contradiction"]["abstention_rate"] == 1.0
    assert report["type:unanswerable"]["false_answer_rate"] == 0.0
