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

from tqdm.auto import tqdm

from datasets import Dataset  # type: ignore[attr-defined]
from eval.dataset import EvalItem, load_suite
from eval.persistence import append_jsonl, read_jsonl, write_json_atomic
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
        score_aggregate: dict[str, float] = {}
        for key in rows[0].keys() if rows else []:
            vals = [row[key] for row in rows if isinstance(row.get(key), int | float)]
            if vals:
                score_aggregate[key] = sum(vals) / len(vals)
        return rows, score_aggregate

    return [], {}


def _latest_run_dir(out_root: Path, suite: str) -> Path | None:
    if not out_root.exists():
        return None
    runs = sorted(path for path in out_root.glob(f"*_{suite}") if path.is_dir())
    return runs[-1] if runs else None


def _select_metrics(metric_names: str) -> list[Any]:
    from ragas.metrics import (
        answer_correctness,
        answer_relevancy,
        context_precision,
        context_recall,
        faithfulness,
    )

    available = {
        "faithfulness": faithfulness,
        "answer_relevancy": answer_relevancy,
        "context_precision": context_precision,
        "context_recall": context_recall,
        "answer_correctness": answer_correctness,
    }
    selected: list[Any] = []
    for raw_name in metric_names.split(","):
        name = raw_name.strip()
        if not name:
            continue
        if name not in available:
            choices = ", ".join(sorted(available))
            raise ValueError(f"Unknown RAGAS metric '{name}'. Choose from: {choices}")
        selected.append(available[name])
    if not selected:
        raise ValueError("At least one RAGAS metric must be selected.")
    return selected


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
    parser.add_argument(
        "--metrics",
        default="faithfulness,context_precision,context_recall",
        help=(
            "Comma-separated RAGAS metrics. Choices: faithfulness, "
            "answer_relevancy, context_precision, context_recall, answer_correctness."
        ),
    )
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

    config = PipelineConfig.from_yaml(args.config).with_env_overrides()
    suite = args.suite or config.evaluation.suite
    corpus_paths, eval_items = load_suite(suite)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_dir = Path(args.out) / f"{timestamp}_{suite}"
    raw_dir = out_dir / "raw"

    pipeline = RAGPipeline(config=config)
    pipeline.add_documents(corpus_paths)

    existing_inputs: dict[str, dict[str, Any]] = {}
    latest_run = _latest_run_dir(Path(args.out), suite)
    if latest_run is not None:
        latest_inputs = latest_run / "raw" / "ragas_inputs.jsonl"
        for raw_item in read_jsonl(latest_inputs):
            if not isinstance(raw_item, dict):
                continue
            item = raw_item.get("item")
            row = raw_item.get("ragas_input")
            if isinstance(item, dict) and isinstance(row, dict) and item.get("id"):
                existing_inputs[str(item["id"])] = row
        if existing_inputs:
            print(f"Resuming with {len(existing_inputs)} existing RAGAS inputs from {latest_run}")
            out_dir = latest_run
            raw_dir = out_dir / "raw"

    rows: list[dict[str, Any]] = []
    for item in tqdm(eval_items, desc=f"Answering {suite}", unit="item"):
        row = existing_inputs.get(item.id)
        if row is None:
            answer = pipeline.answer(item.question)
            row = _answer_to_row(item, answer)
            raw_payload = {"item": item.__dict__, "ragas_input": row}
            write_json_atomic(raw_dir / "inputs" / f"{item.id}.json", raw_payload)
            append_jsonl(raw_dir / "ragas_inputs.jsonl", raw_payload)
        rows.append(row)

    from ragas import evaluate

    ragas_llm, ragas_embeddings = _build_ragas_backends(
        llm_model=args.judge_model,
        embedding_model=args.embedding_model,
        base_url=args.ollama_base_url,
        temperature=0.0,
        num_predict=1024,
    )

    metrics = _select_metrics(args.metrics)

    existing_scores: dict[str, dict[str, Any]] = {}
    for raw_item in read_jsonl(raw_dir / "ragas_scores.jsonl"):
        if not isinstance(raw_item, dict):
            continue
        item_id = raw_item.get("item_id")
        scores = raw_item.get("scores")
        if item_id and isinstance(scores, dict):
            existing_scores[str(item_id)] = scores
    if existing_scores:
        print(f"Resuming with {len(existing_scores)} existing RAGAS scores from {raw_dir}")

    score_rows: list[dict[str, Any]] = []
    for idx, row in enumerate(tqdm(rows, desc="Scoring RAGAS", unit="item")):
        item_id = eval_items[idx].id
        if item_id in existing_scores:
            score_rows.append(existing_scores[item_id])
            continue
        result = evaluate(
            Dataset.from_list([row]),
            metrics=metrics,
            llm=ragas_llm,
            embeddings=ragas_embeddings,
            batch_size=1,
            raise_exceptions=False,
        )
        item_scores, _ = _serialise_scores(result)
        score_row = item_scores[0] if item_scores else {}
        score_rows.append(score_row)
        raw_payload = {"item_id": item_id, "scores": score_row}
        write_json_atomic(raw_dir / "scores" / f"{item_id}.json", raw_payload)
        append_jsonl(raw_dir / "ragas_scores.jsonl", raw_payload)

    aggregate: dict[str, float] = {}
    numeric_keys = {
        key
        for row in score_rows
        for key, value in row.items()
        if isinstance(value, int | float)
    }
    for key in sorted(numeric_keys):
        vals = [row[key] for row in score_rows if isinstance(row.get(key), int | float)]
        if vals:
            aggregate[key] = sum(vals) / len(vals)

    raw_inputs = read_jsonl(raw_dir / "ragas_inputs.jsonl")
    raw_scores = read_jsonl(raw_dir / "ragas_scores.jsonl")
    report_inputs = [
        raw_item["ragas_input"]
        for raw_item in raw_inputs
        if isinstance(raw_item, dict) and isinstance(raw_item.get("ragas_input"), dict)
    ]
    report_scores = [
        raw_item["scores"]
        for raw_item in raw_scores
        if isinstance(raw_item, dict) and isinstance(raw_item.get("scores"), dict)
    ]

    report_path = _write_outputs(
        out_dir=out_dir,
        inputs=report_inputs or rows,
        score_rows=report_scores or score_rows,
        aggregate=aggregate,
        meta={
            "suite": suite,
            "config": args.config,
            "tag": args.tag,
            "timestamp": timestamp,
            "judge_model": args.judge_model,
            "embedding_model": args.embedding_model,
            "ollama_base_url": args.ollama_base_url,
            "metrics": args.metrics,
            "num_corpus_files": len(corpus_paths),
            "num_items": len(eval_items),
        },
    )

    print(f"RAGAS report: {report_path}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
