# Evaluation Report Comparisons

This directory tracks selected report summaries for comparing RAG experiments.
Raw outputs, per-item raw folders, and LLM caches stay local-only.

## Reports

| Folder | Meaning |
|---|---|
| `20260617_hf-llama3-8b_default-prompt_openragbench-30docs_263q` | Hugging Face router run with `meta-llama/Meta-Llama-3-8B-Instruct`, default prompt, Open RAG Benchmark prepared from 30 documents / 263 questions. This run includes many provider quota errors, so use it mainly as evidence that incremental raw/report persistence worked. |
| `20260618_ollama-llama3-1-8b_default-prompt_openragbench-10docs_87q-77scored` | Friend-provided Ollama `llama3.1:8b` RAGAS run using the previous/default prompt. Prepared from 10 documents, which produced 87 questions; 77 questions had RAGAS scores. |
| `20260618_hf-llama3-8b_strict-citation-prompt_smoke_8q` | Local Hugging Face smoke test with `meta-llama/Meta-Llama-3-8B-Instruct` and the new `strict_citation` prompt. Used to validate prompt behavior before asking for another long RAGAS run. |

## Naming Convention

Folders use:

```text
YYYYMMDD_provider-model_prompt_dataset-size_score-coverage
```
