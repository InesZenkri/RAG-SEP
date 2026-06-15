"""RAGAS evaluation entry point.

Run with:
    python -m eval.ragas_run --suite smoke --config configs/ollama-smoke.yaml
"""

from __future__ import annotations

import argparse
import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from datasets import Dataset
from eval.dataset import EvalItem, load_suite
from rag.config import PipelineConfig
from rag.pipeline import RAGPipeline

log = logging.getLogger(__name__)


def _ollama_base_url() -> str:
    raw_host = os.getenv("OLLAMA_HOST", "http://localhost:11434").strip()
    if raw_host.startswith("http://") or raw_host.startswith("https://"):
        return raw_host
    return f"http://{raw_host}"


def _build_ragas_backends(
    *,
    llm_model: str,
    embedding_model: str,
    base_url: str,
    temperature: float,
    num_predict: int,
) -> tuple[Any, Any]:
    from langchain_ollama import ChatOllama, OllamaEmbeddings
    from ragas.embeddings import LangchainEmbeddingsWrapper
    from ragas.llms import LangchainLLMWrapper

    llm = ChatOllama(
        model=llm_model,
        base_url=base_url,
        temperature=temperature,
        num_predict=num_predict,
    )
    embeddings = OllamaEmbeddings(model=embedding_model, base_url=base_url)
    return LangchainLLMWrapper(llm), LangchainEmbeddingsWrapper(embeddings)


def _reference_for(item: EvalItem) -> str:
    if item.expected_answers:
        return item.expected_answers[0]
    return item.answer or ""


def _answer_to_row(item: EvalItem, answer: Any) -> dict[str, Any]:
    contexts = [result.chunk.text for result in answer.retrieved]
    return {
        "user_input": item.question,
        "response": answer.text,
        "retrieved_contexts": contexts,
        "reference": _reference_for(item),
    }


def _serialise_scores(result: Any) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if hasattr(result, "to_pandas"):
        frame = result.to_pandas()
        rows = frame.to_dict(orient="records")
        numeric_cols = frame.select_dtypes(include="number")
        aggregate = {
            str(key): float(value)
            for key, value in numeric_cols.mean(numeric_only=True).to_dict().items()
        }
        return rows, aggregate

    if hasattr(result, "scores"):
        rows = list(result.scores)
        aggregate: dict[str, float] = {}
        for key in rows[0].keys() if rows else []:
            vals = [row[key] for row in rows if isinstance(row.get(key), int | float)]
            if vals:
                aggregate[key] = sum(vals) / len(vals)
        return rows, aggregate

    return [], {}


def _write_outputs(
    *,
    out_dir: Path,
    inputs: list[dict[str, Any]],
    score_rows: list[dict[str, Any]],
    aggregate: dict[str, Any],
    meta: dict[str, Any],
) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "meta": meta,
        "aggregate": aggregate,
        "items": [
            {"input": row, "scores": score_rows[idx] if idx < len(score_rows) else {}}
            for idx, row in enumerate(inputs)
        ],
    }
    json_path = out_dir / "ragas_report.json"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    if score_rows:
        import pandas as pd

        pd.DataFrame(score_rows).to_csv(out_dir / "ragas_scores.csv", index=False)
    Dataset.from_list(inputs).to_json(str(out_dir / "ragas_inputs.jsonl"))
    return json_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run RAGAS on this RAG pipeline.")
    parser.add_argument(
        "--suite",
        default=None,
        choices=["smoke", "full", "adversarial", "robustness"],
    )
    parser.add_argument("--config", default="configs/ollama-smoke.yaml")
    parser.add_argument("--out", default="reports/ragas")
    parser.add_argument("--tag", default=None)
    parser.add_argument("--judge-model", default=os.getenv("RAGAS_JUDGE_MODEL", "llama3.1:8b"))
    parser.add_argument(
        "--embedding-model",
        default=os.getenv("RAGAS_EMBEDDING_MODEL", "nomic-embed-text"),
    )
    parser.add_argument("--ollama-base-url", default=_ollama_base_url())
    parser.add_argument("--batch-size", type=int, default=1)
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

    config = PipelineConfig.from_yaml(args.config).with_env_overrides()
    suite = args.suite or config.evaluation.suite
    corpus_paths, eval_items = load_suite(suite)

    pipeline = RAGPipeline(config=config)
    pipeline.add_documents(corpus_paths)

    rows: list[dict[str, Any]] = []
    for item in eval_items:
        answer = pipeline.answer(item.question)
        rows.append(_answer_to_row(item, answer))

    dataset = Dataset.from_list(rows)

    from ragas import evaluate
    from ragas.metrics import (
        answer_correctness,
        answer_relevancy,
        context_precision,
        context_recall,
        faithfulness,
    )

    ragas_llm, ragas_embeddings = _build_ragas_backends(
        llm_model=args.judge_model,
        embedding_model=args.embedding_model,
        base_url=args.ollama_base_url,
        temperature=0.0,
        num_predict=1024,
    )

    result = evaluate(
        dataset,
        metrics=[
            faithfulness,
            answer_relevancy,
            context_precision,
            context_recall,
            answer_correctness,
        ],
        llm=ragas_llm,
        embeddings=ragas_embeddings,
        batch_size=args.batch_size,
        raise_exceptions=False,
    )

    score_rows, aggregate = _serialise_scores(result)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_dir = Path(args.out) / f"{timestamp}_{suite}"
    report_path = _write_outputs(
        out_dir=out_dir,
        inputs=rows,
        score_rows=score_rows,
        aggregate=aggregate,
        meta={
            "suite": suite,
            "config": args.config,
            "tag": args.tag,
            "timestamp": timestamp,
            "judge_model": args.judge_model,
            "embedding_model": args.embedding_model,
            "ollama_base_url": args.ollama_base_url,
            "num_corpus_files": len(corpus_paths),
            "num_items": len(eval_items),
        },
    )

    print(f"RAGAS report: {report_path}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
