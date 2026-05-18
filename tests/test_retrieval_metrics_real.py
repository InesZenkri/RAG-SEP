from eval.metrics.retrieval import hit_at_k, recall_at_k, mrr, ndcg_at_k
from rag.types import Chunk, RetrievalResult


def make_result(chunk_id: str, doc_id: str, page: int, rank: int) -> RetrievalResult:
    chunk = Chunk(
        chunk_id=chunk_id,
        doc_id=doc_id,
        text=f"Test content for {doc_id} on page {page}.",
        page=page,
    )

    return RetrievalResult(
        chunk=chunk,
        score=1.0,
        rank=rank,
        retriever="test",
    )


def test_hit_at_k_finds_one_correct_result():
    retrieved = [
        make_result("c1", "wrong.pdf", 1, 1),
        make_result("c2", "doc.pdf", 3, 2),
    ]

    gold_keys = {"doc.pdf:p3"}

    assert hit_at_k(retrieved, gold_keys, k=2) == 1.0


def test_recall_at_k_counts_found_gold_keys():
    retrieved = [
        make_result("c1", "doc.pdf", 3, 1),
        make_result("c2", "wrong.pdf", 1, 2),
    ]

    gold_keys = {"doc.pdf:p3", "doc.pdf:p5"}

    assert recall_at_k(retrieved, gold_keys, k=2) == 0.5


def test_mrr_uses_first_correct_rank():
    retrieved = [
        make_result("c1", "wrong.pdf", 1, 1),
        make_result("c2", "wrong.pdf", 2, 2),
        make_result("c3", "doc.pdf", 3, 3),
    ]

    gold_keys = {"doc.pdf:p3"}

    assert mrr(retrieved, gold_keys) == 1 / 3


def test_ndcg_at_k_is_perfect_for_correct_top_result():
    retrieved = [
        make_result("c1", "doc.pdf", 3, 1),
        make_result("c2", "wrong.pdf", 1, 2),
    ]

    gold_keys = {"doc.pdf:p3"}

    assert ndcg_at_k(retrieved, gold_keys, k=2) == 1.0
