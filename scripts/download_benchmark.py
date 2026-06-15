"""Download and prepare Vectara Open RAG Benchmark.

Usage:
    python scripts/download_benchmark.py --subset 50
    python scripts/download_benchmark.py --subset all

The Hugging Face dataset stores processed papers as JSON under
``pdf/arxiv/corpus``. This script downloads those files and prepares a
pipeline-friendly view under ``datasets/open_rag_bench/prepared``:

- ``prepared/corpus/{paper_id}.txt`` for indexing with the existing parser.
- ``prepared/qa.jsonl`` for the existing eval/RAGAS loaders.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from huggingface_hub import HfApi, hf_hub_download, snapshot_download

REPO_ID = "vectara/open_ragbench"
DATASET_DIR = "pdf/arxiv"


def _json_load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _dataset_root(out: Path) -> Path:
    direct = out / DATASET_DIR
    if direct.exists():
        return direct
    official = out / "official" / DATASET_DIR
    if official.exists():
        return official
    raise FileNotFoundError(
        f"Could not find benchmark data under {direct} or {official}."
    )


def _select_corpus_files(subset: str) -> list[str]:
    if subset == "all":
        api = HfApi()
        files = api.list_repo_files(REPO_ID, repo_type="dataset")
        corpus = sorted(
            file
            for file in files
            if file.startswith(f"{DATASET_DIR}/corpus/") and file.endswith(".json")
        )
        return corpus
    try:
        n = int(subset)
    except ValueError as exc:
        raise ValueError("--subset must be an integer or 'all'") from exc
    if n <= 0:
        raise ValueError("--subset must be positive")

    qrels_path = Path(
        hf_hub_download(
            repo_id=REPO_ID,
            repo_type="dataset",
            filename=f"{DATASET_DIR}/qrels.json",
        )
    )
    qrels = _json_load(qrels_path)
    selected_doc_ids: list[str] = []
    seen: set[str] = set()
    for rel in qrels.values():
        doc_id = str((rel or {}).get("doc_id") or "")
        if doc_id and doc_id not in seen:
            seen.add(doc_id)
            selected_doc_ids.append(doc_id)
        if len(selected_doc_ids) >= n:
            break
    return [f"{DATASET_DIR}/corpus/{doc_id}.json" for doc_id in selected_doc_ids]


def _section_text(section: dict[str, Any]) -> str:
    parts: list[str] = []
    text = str(section.get("text") or "").strip()
    if text:
        parts.append(text)
    tables = section.get("tables") or {}
    if isinstance(tables, dict):
        for table_id, table in tables.items():
            table_text = str(table).strip()
            if table_text:
                parts.append(f"\n\nTable {table_id}\n{table_text}")
    images = section.get("images") or {}
    if isinstance(images, dict) and images:
        parts.append(
            "\n\nImage references: "
            + ", ".join(str(image_id) for image_id in images)
        )
    return "\n".join(parts).strip()


def _paper_to_text(paper: dict[str, Any]) -> str:
    parts = [
        f"Title: {paper.get('title', '')}".strip(),
        f"Paper ID: {paper.get('id', '')}".strip(),
    ]
    abstract = str(paper.get("abstract") or "").strip()
    if abstract:
        parts.append(f"Abstract\n{abstract}")

    for section in paper.get("sections") or []:
        section_id = section.get("section_id", "")
        text = _section_text(section)
        if text:
            parts.append(f"Section {section_id}\n{text}")
    return "\n\n".join(part for part in parts if part.strip())


def prepare_dataset(out: Path) -> Path:
    root = _dataset_root(out)
    prepared = out / "prepared"
    prepared_corpus = prepared / "corpus"
    prepared_corpus.mkdir(parents=True, exist_ok=True)

    queries = _json_load(root / "queries.json")
    qrels = _json_load(root / "qrels.json")
    answers = _json_load(root / "answers.json")

    available_docs: set[str] = set()
    for paper_path in sorted((root / "corpus").glob("*.json")):
        paper = _json_load(paper_path)
        paper_id = str(paper.get("id") or paper_path.stem)
        (prepared_corpus / f"{paper_id}.txt").write_text(
            _paper_to_text(paper),
            encoding="utf-8",
        )
        available_docs.add(paper_id)

    qa_path = prepared / "qa.jsonl"
    num_items = 0
    with qa_path.open("w", encoding="utf-8") as handle:
        for query_id, query_meta in queries.items():
            rel = qrels.get(query_id) or {}
            doc_id = str(rel.get("doc_id") or "")
            if doc_id not in available_docs:
                continue
            answer = answers.get(query_id)
            item = {
                "id": str(query_id),
                "question": query_meta.get("query", ""),
                "answer": answer,
                "expected_answers": [answer] if answer else [],
                "doc_ids": [doc_id],
                "doc_sources": [f"{doc_id}.txt"],
                "pages": [1],
                "type": query_meta.get("type", "abstractive"),
                "source": query_meta.get("source"),
                "section_id": rel.get("section_id"),
                "benchmark": "open_rag_bench",
            }
            handle.write(json.dumps(item, ensure_ascii=False) + "\n")
            num_items += 1

    manifest = {
        "repo_id": REPO_ID,
        "dataset_dir": DATASET_DIR,
        "num_documents": len(available_docs),
        "num_questions": num_items,
        "prepared_corpus": str(prepared_corpus),
        "qa_jsonl": str(qa_path),
    }
    (prepared / "manifest.json").write_text(
        json.dumps(manifest, indent=2),
        encoding="utf-8",
    )
    return prepared


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--subset", default="50", help="Number of papers, or 'all'.")
    parser.add_argument("--out", default="datasets/open_rag_bench")
    parser.add_argument(
        "--no-prepare",
        action="store_true",
        help="Only download files; do not create prepared corpus/qa files.",
    )
    args = parser.parse_args()

    out = Path(args.out)
    corpus_files = _select_corpus_files(args.subset)
    allow_patterns = [
        "README.md",
        f"{DATASET_DIR}/answers.json",
        f"{DATASET_DIR}/queries.json",
        f"{DATASET_DIR}/qrels.json",
        f"{DATASET_DIR}/pdf_urls.json",
        *corpus_files,
    ]

    snapshot_download(
        repo_id=REPO_ID,
        repo_type="dataset",
        local_dir=str(out),
        allow_patterns=allow_patterns,
    )

    if args.no_prepare:
        print(f"Downloaded benchmark files to {out}")
        return 0

    prepared = prepare_dataset(out)
    print(f"Prepared benchmark at {prepared}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
