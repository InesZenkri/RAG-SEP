# Reliable PDF Search Agent - SEP 2026 Group 2

A modular Retrieval-Augmented Generation (RAG) system for answering questions
over collections of PDF documents, with grounded citations, explicit
abstention when evidence is weak, and a reproducible evaluation pipeline.

Project documentation and submitted PDFs are maintained in the companion
documentation repository:
https://git.rz.tu-bs.de/isf/sep/sep-2026/iai_drpsa_pdf-search-agent_g2/abgaben/-/tree/main/submission-pdfs?ref_type=heads

> This repository now contains the baseline implementation plus several
> milestone extensions. Some advanced modules still intentionally contain
> `NotImplementedError` and are tracked in the milestone table below.

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env          # add your GEMINI_API_KEY (optional)
pytest                         # unit tests; some future-milestone tests are skipped
python -m eval.run --suite smoke --config configs/baseline.yaml
```

## Repository layout

```
code/
  configs/                # YAML pipeline configs (baseline, hybrid, rerank)
  datasets/
    sample/               # tiny in-repo corpus + QA (drives tests & smoke suite)
    adversarial/          # unanswerable + contradiction cases (M5 / M7)
    open_rag_bench/       # populated by scripts/download_benchmark.py (gitignored)
  reports/runs/           # timestamped eval outputs (JSON + Markdown)
  scripts/                # one-off utilities (benchmark download, adversarial build)
  src/
    rag/
      ingest/             # PDF parser, header/footer cleaner, tables, OCR
      chunking/           # recursive, layout-aware, semantic
      retrieval/          # dense, BM25, hybrid (RRF), cross-encoder reranker
      generation/         # LLM clients (Gemini/HF/echo), prompt, citations,
                          # abstention, confidence
      pipeline.py         # orchestrator
      config.py, types.py # dataclass schemas shared across layers
      cache.py, cost.py   # prompt cache + token-to-euro helpers
      logging_utils.py    # JSON logging + step timer
    eval/
      dataset.py          # EvalItem + JSONL/suite loaders
      metrics/            # retrieval, answer, grounding, abstention,
                          # robustness, efficiency
      judge.py            # LLM-as-judge for abstractive answers
      benchmarks/         # sample + Open RAG Benchmark adapters
      report.py, run.py   # report rendering + CLI entry point
    api/                  # FastAPI app (/query, /index, /stats, /health)
    ui/                   # Streamlit management dashboard
  tests/                  # pytest suite (mirrors src/ layout)
  .gitlab-ci.yml          # lint + unit tests + smoke-eval regression gate
  Makefile                # install / test / smoke / eval / api / ui targets
  pyproject.toml          # pytest, ruff, mypy config
  requirements.txt        # runtime deps
  requirements-dev.txt    # runtime + dev deps
  .env.example            # environment variables template
```

## Stack

| Component            | Choice                                     | Why |
|----------------------|--------------------------------------------|-----|
| Language             | Python 3.11                                | Brief recommends Python |
| PDF parsing          | PyMuPDF + pdfplumber fallback              | Fast + good at tables |
| Chunking             | Recursive character split with overlap     | Simple, strong baseline |
| Embeddings           | sentence-transformers / `all-MiniLM-L6-v2` | Free, CPU-friendly |
| Lexical retrieval    | `rank_bm25`                                 | Reference BM25 |
| Vector store         | In-memory (default) + Chroma (persistent)  | Zero-setup default |
| Reranker             | `BAAI/bge-reranker-base` (optional, M4)    | Standard cross-encoder |
| LLM generator        | **Gemini** (free tier) via `google-genai`  | See below |
| LLM judge            | `gemini-1.5-pro` (or HF for independence)  | Different family than generator |
| Eval                 | Custom harness + JSONL datasets            | Six required metric categories |
| Backend              | FastAPI + Uvicorn                          | Lightweight + async |
| UI                   | Streamlit                                  | Fastest path to a demo |
| Tests / CI           | pytest + GitLab CI                         | Matches submission repo |

### Why Gemini (not Groq)?

Both have free tiers, but for this project Gemini is the better default:

- **Larger free quota**: `gemini-1.5-flash` allows roughly 1500 requests/day
  free, which is enough for a full evaluation run on the Open RAG Benchmark.
  Groq's free tier is rate-limited per minute and per day, which makes batch
  evaluation fragile.
- **Multimodal native**: Gemini accepts PDF pages, tables, and figures as
  inputs directly. The brief mentions multimodal questions (text + tables +
  images) in the Open RAG Benchmark, so this matters.
- **Named in the brief**: the project description explicitly lists Gemini
  free as a recommended provider; using it avoids re-justification.
- **Two model tiers from one SDK**: `flash` as generator, `pro` as judge,
  which is enough model-family separation to reduce judge bias.

Provider choice is abstracted behind `rag.generation.llm_client.LLMClient`;
swapping to Groq, a HuggingFace endpoint, or a local Ollama instance is a
config change, not a code change.

## Datasets

- **`datasets/sample/`**: a small hand-written corpus (photosynthesis,
  mitochondria, transformers) + 8 QA pairs. Drives every unit test and the
  `smoke` eval suite. Stays in git.
- **`datasets/adversarial/`**: unanswerable questions (for abstention
  metrics) and a coffee / type-2-diabetes contradiction pair. Stays in git.
- **`datasets/open_rag_bench/`**: the Vectara benchmark (1000 arXiv PDFs +
  3045 QA pairs). Downloaded on demand via
  `python scripts/download_benchmark.py --subset 50`. **Gitignored.**

## Milestones

| ID | Focus | Status |
|----|-------|--------|
| M0 | Repo scaffold, stack decided, stubs in place | done |
| M1 | Evaluation harness for all six metric categories | partially done - JSONL suite loading, smoke/adversarial suite wiring, eval CLI/report output, and retrieval/answer/grounding/abstention/efficiency metrics are in place; robustness slicing, LLM judge, and Open RAG benchmark adapter/download still need completion |
| M2 | Baseline RAG v1 (ingest -> MiniLM -> Gemini) | partially done - text/PDF parsing, recursive chunking, BM25-backed pipeline, prompt building, citation extraction, Gemini/Ollama/HuggingFace/Echo clients, cost/latency traces, and API query/index flow are implemented; MiniLM dense retrieval factory, prompt cache, abstention decision, citation validation, and confidence scoring still need completion |
| M3 | PDF-parsing robustness (headers, tables, OCR) | partially done - PyMuPDF parsing and repeated header/footer stripping are implemented; table extraction, OCR fallback, and layout/semantic chunking remain pending |
| M4 | Hybrid retrieval + reranker | partially done - BM25 retriever with rank_bm25 or pure-Python fallback is implemented; dense retriever is started; hybrid fusion and cross-encoder reranking remain pending |
| M5 | Strict citations + calibrated confidence | partially done - default prompt enforces `[doc_id:pN]` citations and citation extraction exists; strict prompt, citation validation, abstention rules, and calibrated confidence remain pending |
| M6 | Streamlit management UI | done - corpus upload/path indexing, chat playground, citation display with page previews, traces, and latest evaluation report views are implemented |
| M7 | Robustness + adversarial suite | partially done - adversarial JSONL files and suite loader exist; robustness metrics/reporting remain pending |
| M8 | Full benchmark run, ablation table, final report | pending |

See the full plan for per-milestone deliverables and the CI regression-gate
strategy.

## Team split

- **A - Ingestion**: `rag/ingest/*`, `rag/chunking/*`, adversarial corpus.
- **B - Retrieval**: `rag/retrieval/*`, `eval/metrics/retrieval.py`.
- **C - Generation**: `rag/generation/*`, `eval/metrics/answer.py`,
  `eval/metrics/grounding.py`, `eval/judge.py`.
- **D - Platform**: `src/api/`, `src/ui/`, `eval/report.py`, `eval/run.py`,
  GitLab CI, cost/latency instrumentation.

Everyone contributes to `tests/` and to the final written report.

## Make targets

| Target           | What it does                                           |
|------------------|--------------------------------------------------------|
| `make install`   | Install runtime deps.                                  |
| `make install-dev` | Install runtime + dev deps.                          |
| `make test`      | Run pytest.                                            |
| `make lint`      | Ruff + mypy.                                           |
| `make smoke`     | Run the smoke eval against `configs/baseline.yaml`.    |
| `make eval`      | Run the full eval against `configs/baseline.yaml`.     |
| `make api`       | Launch the FastAPI backend.                            |
| `make ui`        | Launch the Streamlit UI.                               |

## Contacts

- Baptiste Bremond  - `baptiste.bremond@tu-braunschweig.de`
- Michel Besserve   - `michel.besserve@tu-braunschweig.de`
