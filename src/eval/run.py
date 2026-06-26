"""Eval entry point: python -m eval.run --suite smoke --config configs/baseline.yaml"""

from __future__ import annotations

import argparse
import logging
import random
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from tqdm.auto import tqdm
except ImportError:  # pragma: no cover - optional progress bar dependency
    def tqdm(iterable, *args, **kwargs):
        return iterable

from eval.dataset import EvalItem, load_suite
from eval.metrics.answer import exact_match, token_f1
from eval.metrics.efficiency import summarise_efficiency
from eval.metrics.grounding import citation_precision, citation_recall
from eval.metrics.retrieval import hit_at_k
from eval.persistence import append_jsonl, read_jsonl, write_json_atomic
from eval.report import build_report, write_report
from rag.config import PipelineConfig
from rag.logging_utils import setup_logging, timed
from rag.types import Answer

log = logging.getLogger(__name__)


def _try_pipeline_index(pipeline: Any, corpus: list[Path]) -> float:
    """Index the corpus and return elapsed ms. Returns 0 if not implemented yet."""
    index_time: dict[str, float] = {}
    try:
        with timed(index_time, "index"):
            pipeline.add_documents([str(p) for p in corpus])
        return index_time["index"]
    except NotImplementedError:
        log.warning("pipeline.add_documents() not yet implemented — skipping indexing.")
        return 0.0


def _try_pipeline_answer(pipeline: Any, item: EvalItem) -> tuple[Answer | None, str]:
    """Run the pipeline on one question. Returns (None, error) if not implemented yet."""
    try:
        answer = pipeline.answer(item.question)
        return answer, ""
    except NotImplementedError:
        return None, "NotImplementedError"
    except Exception as exc:  # noqa: BLE001
        log.exception("Unexpected error answering item %s", item.id)
        return None, str(exc)


def _stub_answer(item: EvalItem) -> Answer:
    """Placeholder answer used when the pipeline is not ready yet."""
    return Answer(question=item.question, text="", abstained=True)


def _gold_retrieval_keys(item: EvalItem) -> set[str]:
    return {
        f"{Path(src).stem}:p{p}"
        for src in item.doc_sources
        for p in (item.pages or [1])
    }


def _compute_retrieval(pairs: list[tuple[EvalItem, Answer]]) -> dict[str, Any]:
    try:
        from eval.metrics.retrieval import mrr, ndcg_at_k, recall_at_k
        k = 5
        results: dict[str, float] = {}
        all_recall, all_mrr, all_ndcg, all_hit = [], [], [], []
        for item, answer in pairs:
            gold_keys = _gold_retrieval_keys(item)
            all_recall.append(recall_at_k(answer.retrieved, gold_keys, k))
            all_mrr.append(mrr(answer.retrieved, gold_keys))
            all_ndcg.append(ndcg_at_k(answer.retrieved, gold_keys, k))
            all_hit.append(hit_at_k(answer.retrieved, gold_keys, k))
        n = len(pairs) or 1
        results[f"recall@{k}"] = sum(all_recall) / n
        results["mrr"] = sum(all_mrr) / n
        results[f"ndcg@{k}"] = sum(all_ndcg) / n
        results[f"hit@{k}"] = sum(all_hit) / n
        return results
    except NotImplementedError:
        log.warning("Retrieval metrics not yet implemented.")
        return {"status": "not_implemented"}


def _compute_answer(pairs: list[tuple[EvalItem, Answer]]) -> dict[str, Any]:
    try:
        all_em, all_f1 = [], []
        for item, answer in pairs:
            refs = item.expected_answers or ([item.answer] if item.answer else [])
            if not refs:
                continue
            all_em.append(exact_match(answer.text, refs))
            all_f1.append(token_f1(answer.text, refs))
        n = len(all_em) or 1
        return {"exact_match": sum(all_em) / n, "token_f1": sum(all_f1) / n}
    except NotImplementedError:
        log.warning("Answer quality metrics not yet implemented.")
        return {"status": "not_implemented"}


def _compute_grounding(pairs: list[tuple[EvalItem, Answer]]) -> dict[str, Any]:
    try:
        precs, recalls = [], []
        for _, answer in pairs:
            precs.append(citation_precision(answer))
            recalls.append(citation_recall(answer))
        n = len(pairs) or 1
        return {
            "citation_precision": sum(precs) / n,
            "citation_recall": sum(recalls) / n,
        }
    except NotImplementedError:
        log.warning("Grounding metrics not yet implemented.")
        return {"status": "not_implemented"}


def _compute_abstention(pairs: list[tuple[EvalItem, Answer]]) -> dict[str, Any]:
    try:
        from eval.metrics.abstention import false_answer_rate, false_refusal_rate
        return {
            "false_refusal_rate": false_refusal_rate(pairs),
            "false_answer_rate": false_answer_rate(pairs),
        }
    except NotImplementedError:
        log.warning("Abstention metrics not yet implemented.")
        return {"status": "not_implemented"}


def _compute_robustness(pairs: list[tuple[EvalItem, Answer]]) -> dict[str, Any]:
    try:
        from eval.metrics.robustness import robustness_report
        return robustness_report(pairs)
    except NotImplementedError:
        log.warning("Robustness metrics not yet implemented.")
        return {"status": "not_implemented"}


def _per_item_result(item: EvalItem, answer: Answer, error: str) -> dict[str, Any]:
    refs = item.expected_answers or ([item.answer] if item.answer else [])
    gold_keys = _gold_retrieval_keys(item)
    retrieved_keys = {result.chunk.citation_key() for result in answer.retrieved}
    invalid_citations = [
        citation.key()
        for citation in answer.citations
        if citation.key() not in retrieved_keys
    ]

    item_exact_match = exact_match(answer.text, refs) if refs else None
    item_token_f1 = token_f1(answer.text, refs) if refs else None
    item_retrieval_hit = hit_at_k(answer.retrieved, gold_keys, k=5)
    item_citation_precision = citation_precision(answer)
    item_citation_recall = citation_recall(answer)

    issues = []
    if error:
        issues.append("error")
    if answer.abstained:
        issues.append("abstained")
    if item_retrieval_hit < 1.0:
        issues.append("retrieval_miss")
    if item_token_f1 is not None and item_token_f1 < 0.5:
        issues.append("low_answer_f1")
    if answer.citations and item_citation_precision < 1.0:
        issues.append("unsupported_citation")
    if invalid_citations:
        issues.append("invalid_citation_id")
    if answer.text.strip().startswith("[") and answer.text.strip().endswith("]"):
        issues.append("citation_only_answer")

    return {
        "id": item.id,
        "type": item.type,
        "question": item.question,
        "gold_answer": item.answer,
        "predicted": answer.text,
        "abstained": answer.abstained,
        "confidence": answer.confidence,
        "retrieval_hit@5": item_retrieval_hit,
        "exact_match": item_exact_match,
        "token_f1": item_token_f1,
        "citation_precision": item_citation_precision,
        "citation_recall": item_citation_recall,
        "gold_retrieval_keys": sorted(gold_keys),
        "retrieved": [
            {
                "rank": result.rank,
                "chunk_id": result.chunk.chunk_id,
                "doc_id": result.chunk.doc_id,
                "page": result.chunk.page,
                "score": result.score,
                "retriever": result.retriever,
            }
            for result in answer.retrieved
        ],
        "citations": [
            {
                "doc_id": citation.doc_id,
                "page": citation.page,
                "chunk_id": citation.chunk_id,
                "quote": citation.quote,
                "valid_retrieved_key": citation.key() in retrieved_keys,
            }
            for citation in answer.citations
        ],
        "invalid_citations": invalid_citations,
        "issues": issues,
        "latency_ms": answer.latency_ms,
        "cost_eur": answer.cost_eur,
        "error": error,
    }


def main(argv: list[str] | None = None) -> int:  # noqa: C901
    parser = argparse.ArgumentParser(description="Run the RAG evaluation suite.")
    parser.add_argument(
        "--suite", default=None,
        choices=["smoke", "full", "adversarial", "robustness"],
    )
    parser.add_argument("--config", default="configs/baseline.yaml")
    parser.add_argument("--out", default=None)
    parser.add_argument("--tag", default=None, help="Optional run label.")
    parser.add_argument("--json-logs", action="store_true", help="Emit JSON log lines.")
    args = parser.parse_args(argv)

    config = PipelineConfig.from_yaml(args.config).with_env_overrides()
    suite = args.suite or config.evaluation.suite
    out_root = args.out or config.evaluation.output_dir
    random.seed(config.evaluation.seed)

    setup_logging(json_output=args.json_logs)
    log.info("Starting eval run: suite=%s config=%s tag=%s", suite, args.config, args.tag)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_dir = Path(out_root) / f"{timestamp}_{suite}"
    raw_dir = out_dir / "raw"

    corpus_paths, eval_items = load_suite(suite)
    log.info("Suite '%s': %d corpus files, %d eval items", suite, len(corpus_paths), len(eval_items))

    try:
        from rag.pipeline import RAGPipeline
        pipeline: Any = RAGPipeline(config=config)
    except NotImplementedError:
        log.warning("RAGPipeline not yet implemented — answers will be stubs.")
        pipeline = None

    index_build_ms = 0.0
    if pipeline is not None:
        index_build_ms = _try_pipeline_index(pipeline, corpus_paths)
        log.info("Indexing complete in %.0f ms", index_build_ms)

    pairs: list[tuple[EvalItem, Answer]] = []
    answers: list[Answer] = []
    per_item: list[dict[str, Any]] = []
    num_errors = 0

    for item in tqdm(eval_items, desc=f"Answering {suite}", unit="item"):
        if pipeline is not None:
            answer, error = _try_pipeline_answer(pipeline, item)
        else:
            answer, error = None, "pipeline_not_ready"

        if answer is None:
            answer = _stub_answer(item)
            num_errors += 1

        pairs.append((item, answer))
        answers.append(answer)

        item_result = _per_item_result(item, answer, error)
        per_item.append(item_result)
        raw_payload = {"item": item.__dict__, "result": item_result}
        write_json_atomic(raw_dir / "items" / f"{item.id}.json", raw_payload)
        append_jsonl(raw_dir / "items.jsonl", raw_payload)

    log.info("Answered %d items (%d errors/stubs)", len(eval_items), num_errors)

    metric_fns = {
        "retrieval": lambda: _compute_retrieval(pairs),
        "answer": lambda: _compute_answer(pairs),
        "grounding": lambda: _compute_grounding(pairs),
        "abstention": lambda: _compute_abstention(pairs),
        "robustness": lambda: _compute_robustness(pairs),
        "efficiency": lambda: summarise_efficiency(answers, index_build_ms).to_dict(),
    }
    metrics: dict[str, Any] = {}
    for metric in tqdm(config.evaluation.metrics, desc="Computing metrics", unit="metric"):
        compute = metric_fns.get(metric)
        if compute is None:
            log.warning("Unknown configured metric '%s' - skipping.", metric)
            continue
        metrics[metric] = compute()

    run_meta: dict[str, Any] = {
        "suite": suite,
        "benchmark": config.evaluation.benchmark,
        "config": args.config,
        "config_name": config.name,
        "seed": config.evaluation.seed,
        "tag": args.tag,
        "timestamp": timestamp,
        "num_corpus_files": len(corpus_paths),
        "num_items": len(eval_items),
        "num_errors": num_errors,
    }

    raw_items = read_jsonl(raw_dir / "items.jsonl")
    report_items = [
        raw_item["result"]
        for raw_item in raw_items
        if isinstance(raw_item, dict) and isinstance(raw_item.get("result"), dict)
    ]
    report = build_report(run_meta, metrics, report_items or per_item)
    json_path = write_report(report, out_dir)

    log.info("Report written to %s", out_dir)
    print(f"Report: {json_path}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
