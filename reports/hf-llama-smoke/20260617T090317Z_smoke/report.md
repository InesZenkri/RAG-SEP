# Eval Report — smoke

| Field | Value |
|-------|-------|
| Config | `configs/baseline.yaml` |
| Tag | hf-llama-real-test-2 |
| Generated | 2026-06-17T09:03:39.848516+00:00 |
| Items | 8 |
| Errors | 0 |

## Metric Snapshot

| Category | Metric | Value | Status |
|----------|--------|-------|--------|
| retrieval | recall@5 | 1.0000 | good |
| retrieval | mrr | 1.0000 | good |
| answer | exact_match | 0.0000 | needs work |
| answer | token_f1 | 0.6342 | needs work |
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
| token_f1 | 0.6342 |

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
| index_build_ms | 9923.6000 |
| avg_latency_ms / generation | 1409.23 |
| avg_latency_ms / rerank | 0.00 |
| avg_latency_ms / retrieval | 77.27 |
| p95_latency_ms / generation | 4175.70 |
| p95_latency_ms / rerank | 0.00 |
| p95_latency_ms / retrieval | 199.25 |
| avg_tokens / input | 544.60 |
| avg_tokens / output | 18.00 |
| total_cost_eur | 0.0000 |
| peak_memory_mb | 0.0000 |

## Per-Item Results

| id | type | retrieval | em | f1 | citation precision | issues |
|----|------|-----------|----|----|--------------------|--------|
| q1 | extractive | 1.0000 | 0.0000 | 0.4286 | 1.0000 | low_answer_f1 |
| q2 | extractive | 1.0000 | 0.0000 | 0.5714 | 1.0000 | none |
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
- Predicted: The products of photosynthesis are glucose (C6H12O6) and oxygen (6 O2). [photosynthesis:p1]
- Issues: low_answer_f1
- Gold retrieval keys: `photosynthesis:p1`
- Top retrieved: `#1 photosynthesis:p1 (0.704)`, `#2 mitochondria:p1 (0.270)`, `#3 transformers:p1 (0.083)`
- Citations: `photosynthesis:p1` (valid)

### q7

- Question: What does the Calvin cycle produce?
- Gold: glyceraldehyde-3-phosphate
- Predicted: The Calvin cycle fixes carbon dioxide into a three-carbon sugar called glyceraldehyde-3-phosphate. [photosynthesis:p1]
- Issues: low_answer_f1
- Gold retrieval keys: `photosynthesis:p1`
- Top retrieved: `#1 photosynthesis:p1 (0.649)`, `#2 mitochondria:p1 (0.331)`, `#3 transformers:p1 (0.038)`
- Citations: `photosynthesis:p1` (valid)
