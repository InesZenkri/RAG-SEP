# Eval Report — smoke

| Field | Value |
|-------|-------|
| Config | `configs/hf-strict-smoke.yaml` |
| Tag | hf-strict-prompt-smoke-v2 |
| Generated | 2026-06-18T10:04:51.762585+00:00 |
| Items | 8 |
| Errors | 0 |

## Metric Snapshot

| Category | Metric | Value | Status |
|----------|--------|-------|--------|
| retrieval | recall@5 | 1.0000 | good |
| retrieval | mrr | 1.0000 | good |
| answer | exact_match | 0.0000 | needs work |
| answer | token_f1 | 0.6397 | needs work |
| grounding | citation_precision | 1.0000 | good |
| grounding | citation_recall | 1.0000 | good |
| abstention | false_refusal_rate | 0.0000 | good |
| abstention | false_answer_rate | 0.0000 | good |

## Retrieval
| Metric | Value |
|--------|-------|
| recall@5 | 1.0000 |
| mrr | 1.0000 |
| ndcg@5 | 1.0000 |
| hit@5 | 1.0000 |

## Answer
| Metric | Value |
|--------|-------|
| exact_match | 0.0000 |
| token_f1 | 0.6397 |

## Grounding
| Metric | Value |
|--------|-------|
| citation_precision | 1.0000 |
| citation_recall | 1.0000 |

## Abstention
| Metric | Value |
|--------|-------|
| false_refusal_rate | 0.0000 |
| false_answer_rate | 0.0000 |

## Robustness
| Metric | Value |
|--------|-------|
| status | not_implemented |

## Efficiency
| Metric | Value |
|--------|-------|
| num_queries | 8 |
| index_build_ms | 4.5800 |
| avg_latency_ms / generation | 1394.65 |
| avg_latency_ms / rerank | 0.00 |
| avg_latency_ms / retrieval | 0.30 |
| p95_latency_ms / generation | 2287.95 |
| p95_latency_ms / rerank | 0.00 |
| p95_latency_ms / retrieval | 0.55 |
| avg_tokens / input | 703.60 |
| avg_tokens / output | 17.80 |
| total_cost_eur | 0.0000 |
| peak_memory_mb | 0.0000 |

## Per-Item Results

| id | type | retrieval | em | f1 | citation precision | issues |
|----|------|-----------|----|----|--------------------|--------|
| q1 | extractive | 1.0000 | 0.0000 | 0.4286 | 1.0000 | low_answer_f1 |
| q2 | extractive | 1.0000 | 0.0000 | 0.6154 | 1.0000 | none |
| q3 | extractive | 1.0000 | 0.0000 | 0.6667 | 1.0000 | none |
| q4 | extractive | 1.0000 | 0.0000 | 0.8571 | 1.0000 | none |
| q5 | extractive | 1.0000 | 0.0000 | 0.9091 | 1.0000 | none |
| q6 | extractive | 1.0000 | 0.0000 | 0.6667 | 1.0000 | none |
| q7 | extractive | 1.0000 | 0.0000 | 0.3077 | 1.0000 | low_answer_f1 |
| q8 | extractive | 1.0000 | 0.0000 | 0.6667 | 1.0000 | none |

## Per-Item Diagnostics

### q1

- Question: What are the products of photosynthesis?
- Gold: glucose and oxygen
- Predicted: The products of photosynthesis are glucose (C6H12O6) and oxygen (6 O2) [photosynthesis:p1].
- Issues: low_answer_f1
- Gold retrieval keys: `photosynthesis:p1`
- Top retrieved: `#1 photosynthesis:p1 (0.849)`, `#2 mitochondria:p1 (0.430)`, `#3 transformers:p1 (0.350)`
- Citations: `photosynthesis:p1` (valid)

### q7

- Question: What does the Calvin cycle produce?
- Gold: glyceraldehyde-3-phosphate
- Predicted: The Calvin cycle fixes carbon dioxide into a three-carbon sugar called glyceraldehyde-3-phosphate. [photosynthesis:p1]
- Issues: low_answer_f1
- Gold retrieval keys: `photosynthesis:p1`
- Top retrieved: `#1 photosynthesis:p1 (1.701)`, `#2 mitochondria:p1 (0.390)`, `#3 transformers:p1 (0.174)`
- Citations: `photosynthesis:p1` (valid)
