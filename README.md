# Reliable PDF Search Agent - SEP 2026 Group 2: CoDex

A modular Retrieval-Augmented Generation (RAG) system for answering questions
over collections of PDF documents, with grounded citations, explicit
abstention when evidence is weak, and a reproducible evaluation pipeline.

Project documentation and submitted PDFs are maintained in the
[companion documentation repository](https://git.rz.tu-bs.de/isf/sep/sep-2026/iai_drpsa_pdf-search-agent_g2/abgaben/-/tree/main/submission-pdfs?ref_type=heads).

> This repository contains the implementation code. The project is still under
> active milestone development, so some advanced modules are implemented as
> stubs or are not yet wired into the end-to-end pipeline.

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
pip install -e .
cp .env.example .env          # add your GEMINI_API_KEY (optional)
pytest                         # unit tests; some future-milestone tests are skipped
make smoke                     # CI-compatible smoke eval using the echo provider
```

## Repository layout

```
code/
  configs/                # YAML pipeline/evaluation configs (baseline, hybrid, rerank)
  datasets/
    README.md             # dataset structure and usage notes
    sample/               # tiny in-repo corpus + QA (drives tests & smoke suite)
    adversarial/          # unanswerable + contradiction cases (M5 / M7)
    open_rag_bench/       # reserved for downloaded Open RAG Benchmark data (gitignored)
  reports/                # timestamped eval outputs (JSON + Markdown)
  scripts/                # one-off utilities (benchmark download, adversarial build)
  src/
    rag/
      ingest/             # PDF parser, header/footer cleaner, tables, OCR
      chunking/           # recursive, layout-aware, semantic
      retrieval/          # dense, BM25, hybrid (RRF), cross-encoder reranker
      generation/         # LLM clients (Gemini/HF/Ollama/echo), prompt, citations,
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
      assets/             # UI images and static assets
  tests/                  # pytest suite (mirrors src/ layout)
  .uploads/               # local uploaded documents used by the UI/API
  .gitlab-ci.yml          # lint + unit tests + smoke-eval regression gate
  Makefile                # install / test / smoke / eval / api / ui targets
  pyproject.toml          # pytest, ruff, mypy config
  requirements.txt        # runtime deps
  requirements-dev.txt    # runtime + dev deps
  .env.example            # environment variables template
```

## Stack

| Component            | Current choice/status                       | Notes |
|----------------------|---------------------------------------------|-------|
| Language             | Python 3.10+                                | `pyproject.toml` requires Python >= 3.10 |
| PDF parsing          | PyMuPDF, cleaner utilities, table/OCR stubs | Core parsing works; table extraction and OCR fallback are milestone work |
| Chunking             | Recursive chunking                          | Layout-aware and semantic chunking are present as modules but not finished |
| Retrieval            | BM25, dense, and hybrid RRF retrievers      | Hybrid retrieval is available through the retriever factory; cross-encoder reranking is still pending |
| Embeddings           | `sentence-transformers` models              | Baseline YAML uses `all-MiniLM-L6-v2`; hybrid/rerank use `BAAI/bge-small-en-v1.5` |
| Vector store         | In-memory default, Chroma planned           | Persistent store settings exist in config; full persistence is not the default path yet |
| LLM generator        | Gemini, Hugging Face, Ollama, or Echo       | Provider selected by YAML/environment; baseline uses Echo for CI-safe smoke runs |
| LLM judge            | Configured judge section, implementation stub | Judge parameters are in YAML; actual judge scoring still needs implementation |
| Eval                 | Custom JSONL harness and report writer      | Smoke/adversarial suite loading, core metrics, per-item diagnostics, and JSON/Markdown reports exist; benchmark download/adapter still pending |
| Backend              | FastAPI + Uvicorn                           | `/query`, `/index`, `/stats`, `/health` style API |
| UI                   | Streamlit                                   | Upload/index, chat, traces, and eval report views |
| Tests / CI           | pytest + GitLab CI                          | Several milestone tests are intentionally skipped until their modules are complete |

### LLM Provider Strategy

Provider choice is abstracted behind `rag.generation.llm_client.LLMClient` and
selected through YAML plus environment overrides. The current setup uses:

- **Gemini** as the default hosted provider for normal generation and judge
  runs. `gemini-2.5-flash` is used for generation-oriented runs, while
  `gemini-2.5-pro` is configured as the judge model.
- **Hugging Face Inference** as a hosted fallback when Gemini is unavailable
  or when a separate model family is useful for comparison.
- **Ollama** as the local/cluster provider path. This is the direction for
  runs on the institute cluster where models can be hosted through an Ollama
  endpoint instead of an external API.
- **Echo** as an offline stub for CI, smoke runs, and development without API
  credentials. Echo verifies indexing, retrieval, report generation, and the
  end-to-end control flow, but it does not measure real answer quality.

Switching provider or model is a configuration change: set
`generation.provider` / `generation.model` in YAML or override the provider
with `RAG_GENERATION_PROVIDER`. For Ollama, set `OLLAMA_HOST` to the local or
cluster endpoint.

### Evaluation Modes

The project currently uses two different evaluation modes:

- **CI smoke evaluation**: `make smoke` / GitLab `smoke-eval` runs
  `configs/baseline.yaml`, which uses `generation.provider: echo`. This mode is
  deterministic and does not need API keys or a GPU. Its retrieval, efficiency,
  and report-generation results are meaningful; answer and grounding quality
  are expected to be poor because Echo returns a simulated answer.
- **Real generation evaluation**: local or cluster runs can set
  `RAG_GENERATION_PROVIDER=gemini`, `ollama`, or `huggingface`. These reports
  should be used for answer quality and citation quality. Recent smoke runs with
  a real/local model reached perfect retrieval on the sample suite and strong
  answer/grounding scores.

Reports are written to `reports/runs/<timestamp>_<suite>/report.json` and
`report.md`. The JSON and Markdown reports include aggregate metrics plus
per-item diagnostics: retrieved chunks, parsed citations, invalid citations,
per-question answer scores, retrieval hits, latency, and issue labels.

## Datasets

- **`datasets/sample/`**: a small hand-written corpus (photosynthesis,
  mitochondria, transformers) + 8 QA pairs. Drives the `smoke` eval suite and
  test fixtures. Stays in git.
- **`datasets/adversarial/`**: unanswerable questions (for abstention
  metrics) and a coffee / type-2-diabetes contradiction pair. Stays in git.
- **`datasets/open_rag_bench/`**: the Vectara benchmark (1000 arXiv PDFs +
  3045 QA pairs). This directory is gitignored and reserved for the downloaded
  benchmark. The download script and adapter are still milestone work.

## Current Status

Implemented and usable now:

- YAML-driven runtime and evaluation configuration in `configs/`.
- PDF/text parsing, recursive chunking, BM25 retrieval, an initial dense
  retriever, and RRF-based hybrid retrieval.
- LLM client abstraction for Gemini, Hugging Face, Ollama, and Echo.
- Prompt construction, citation extraction and validation, abstention helper
  logic, confidence heuristic, token/cost tracing, and disk-backed prompt
  caching.
- FastAPI backend and Streamlit management UI.
- Smoke/adversarial JSONL suite loading, core metric functions, per-item
  diagnostics, and JSON/Markdown evaluation reports.
- GitLab CI for Ruff linting, unit tests, and artifact-producing smoke evals.

Still incomplete or not fully wired:

- Cross-encoder reranking.
- Full pipeline/config use of dense and hybrid retrieval modes.
- Calibrated confidence in the final answer flow.
- LLM-as-a-judge execution.
- Open RAG Benchmark download/adapter and full benchmark run.
- Table extraction, OCR fallback, layout-aware chunking, and semantic chunking.

## Milestones

Tracking links point to the GitLab milestone pages.

| ID | Focus | Status | Tracking |
|----|-------|--------|----------|
| M0 | Repo scaffold, stack decided, stubs in place | done | [M0 milestone](https://git.rz.tu-bs.de/isf/sep/sep-2026/iai_drpsa_pdf-search-agent_g2/code/-/milestones/1) |
| M1 | Evaluation harness for all six metric categories | partially done - smoke/adversarial suite loading, YAML-driven eval config, core metrics, per-item diagnostics, Markdown/JSON reports, and CI smoke artifacts exist; robustness slicing, LLM judge execution, and Open RAG Benchmark integration remain pending | [M1 milestone](https://git.rz.tu-bs.de/isf/sep/sep-2026/iai_drpsa_pdf-search-agent_g2/code/-/milestones/2) |
| M2 | Baseline RAG v1 | partially done - parsing, recursive chunking, BM25-backed pipeline, dense retriever, providers, prompt/citation extraction, citation validation helper, disk prompt cache, API flow, abstention helper, and confidence heuristic exist; full dense/hybrid pipeline integration and calibrated confidence remain pending | [M2 milestone](https://git.rz.tu-bs.de/isf/sep/sep-2026/iai_drpsa_pdf-search-agent_g2/code/-/milestones/3) |
| M3 | PDF-parsing robustness | partially done - PyMuPDF parsing and repeated header/footer stripping are implemented; table extraction, OCR fallback, and advanced chunking remain pending | [M3 milestone](https://git.rz.tu-bs.de/isf/sep/sep-2026/iai_drpsa_pdf-search-agent_g2/code/-/milestones/4) |
| M4 | Hybrid retrieval + reranker | partially done - BM25, dense retrieval, RRF hybrid fusion, and factory construction for hybrid mode exist; cross-encoder reranking and full pipeline/config integration remain pending | [M4 milestone](https://git.rz.tu-bs.de/isf/sep/sep-2026/iai_drpsa_pdf-search-agent_g2/code/-/milestones/5) |
| M5 | Strict citations + calibrated confidence | partially done - strict citation prompt/citation extraction, citation validation helper, abstention rules, and confidence heuristic exist; pipeline-level validation integration and calibration remain pending | [M5 milestone](https://git.rz.tu-bs.de/isf/sep/sep-2026/iai_drpsa_pdf-search-agent_g2/code/-/milestones/6) |
| M6 | Streamlit management UI | done - corpus upload/path indexing, chat playground, citation display with page previews, traces, and latest evaluation report views are implemented | [M6 milestone](https://git.rz.tu-bs.de/isf/sep/sep-2026/iai_drpsa_pdf-search-agent_g2/code/-/milestones/7) |
| M7 | Robustness + adversarial suite | partially done - adversarial JSONL files and suite loader exist; robustness metrics/reporting remain pending | [M7 milestone](https://git.rz.tu-bs.de/isf/sep/sep-2026/iai_drpsa_pdf-search-agent_g2/code/-/milestones/8) |
| M8 | Full benchmark run, ablation table, final report | pending | [M8 milestone](https://git.rz.tu-bs.de/isf/sep/sep-2026/iai_drpsa_pdf-search-agent_g2/code/-/milestones/9) |

See the full plan for per-milestone deliverables and the CI regression-gate
strategy.

## Team split

- **Hiba - Ingestion**: `rag/ingest/*`, `rag/chunking/*`, adversarial corpus.
- **Mohammed - Retrieval**: `rag/retrieval/*`, `eval/metrics/retrieval.py`.
- **Finn - Generation**: `rag/generation/*`, `eval/metrics/answer.py`,
  `eval/metrics/grounding.py`, `eval/judge.py`.
- **Ines - Platform & evaluation harness**: `src/api/`, `src/ui/`,
  `eval/run.py`, `eval/report.py`, `eval/dataset.py`,
  `eval/metrics/efficiency.py`, `rag/config.py`, `rag/cost.py`,
  `rag/logging_utils.py`, `configs/*.yaml`, GitLab CI, cost/latency
  instrumentation.

Everyone contributes to `tests/` and to the final written report.

## Make targets

| Target           | What it does                                           |
|------------------|--------------------------------------------------------|
| `make install`   | Install runtime deps.                                  |
| `make install-dev` | Install runtime + dev deps.                          |
| `make test`      | Run pytest.                                            |
| `make lint`      | Ruff + mypy.                                           |
| `make smoke`     | Run the CI-safe smoke eval against `configs/ci-smoke.yaml`. |
| `make eval`      | Run the full eval path against `configs/baseline.yaml`; requires the benchmark adapter/download work to be completed. |
| `make api`       | Launch the FastAPI backend.                            |
| `make ui`        | Launch the Streamlit UI.                               |

See [docs/linting.md](./docs/linting.md) for the linting rules that should be
checked before pushing code changes.

## Contacts

- Baptiste Bremond  - `baptiste.bremond@tu-braunschweig.de`
- Michel Besserve   - `michel.besserve@tu-braunschweig.de`


