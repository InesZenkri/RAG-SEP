# Eval Report — adversarial

| Field | Value |
|-------|-------|
| Config | `configs/baseline.yaml` |
| Tag | hf-llama-adversarial-test |
| Generated | 2026-06-17T09:05:42.716986+00:00 |
| Items | 6 |
| Errors | 0 |

## Metric Snapshot

| Category | Metric | Value | Status |
|----------|--------|-------|--------|
| retrieval | recall@5 | 0.1667 | needs work |
| retrieval | mrr | 0.1667 | needs work |
| answer | exact_match | 0.0000 | needs work |
| answer | token_f1 | 0.0000 | needs work |
| grounding | citation_precision | 0.1667 | needs work |
| grounding | citation_recall | 0.1667 | needs work |
| abstention | false_refusal_rate | 0.0000 | good |
| abstention | false_answer_rate | 0.1667 | ok |

## Retrieval
| Metric | Value |
|--------|-------|
| recall@5 | 0.1667 |
| mrr | 0.1667 |
| ndcg@5 | 0.1667 |
| hit@5 | 0.1667 |

## Answer
| Metric | Value |
|--------|-------|
| exact_match | 0.0000 |
| token_f1 | 0.0000 |

## Grounding
| Metric | Value |
|--------|-------|
| citation_precision | 0.1667 |
| citation_recall | 0.1667 |

## Abstention
| Metric | Value |
|--------|-------|
| false_refusal_rate | 0.0000 |
| false_answer_rate | 0.1667 |

## Robustness
| Metric | Value |
|--------|-------|
| status | not_implemented |

## Efficiency
| Metric | Value |
|--------|-------|
| num_queries | 6 |
| index_build_ms | 8996.8100 |
| avg_latency_ms / generation | 3333.68 |
| avg_latency_ms / rerank | 0.00 |
| avg_latency_ms / retrieval | 84.37 |
| p95_latency_ms / generation | 13106.00 |
| p95_latency_ms / rerank | 0.00 |
| p95_latency_ms / retrieval | 223.63 |
| avg_tokens / input | 190.80 |
| avg_tokens / output | 12.50 |
| total_cost_eur | 0.0000 |
| peak_memory_mb | 0.0000 |

## Per-Item Results

| id | type | retrieval | em | f1 | citation precision | issues |
|----|------|-----------|----|----|--------------------|--------|
| u1 | unanswerable | 0.0000 | - | - | 0.0000 | abstained, retrieval_miss |
| u2 | unanswerable | 0.0000 | - | - | 0.0000 | abstained, retrieval_miss |
| u3 | unanswerable | 0.0000 | - | - | 0.0000 | abstained, retrieval_miss |
| u4 | unanswerable | 0.0000 | - | - | 0.0000 | abstained, retrieval_miss |
| u5 | unanswerable | 0.0000 | - | - | 0.0000 | abstained, retrieval_miss |
| c1 | contradiction | 1.0000 | - | - | 1.0000 | none |

## Per-Item Diagnostics

### u1

- Question: What is the average annual rainfall in Reykjavík?
- Gold: None
- Predicted: I cannot answer from the provided documents.
- Issues: abstained, retrieval_miss
- Gold retrieval keys: ``
- Top retrieved: `#1 doc_a:p1 (0.068)`, `#2 doc_b:p1 (0.028)`
- Citations: -

### u2

- Question: Who won the 2023 Champions League final?
- Gold: None
- Predicted: I cannot answer from the provided documents.
- Issues: abstained, retrieval_miss
- Gold retrieval keys: ``
- Top retrieved: `#1 doc_a:p1 (0.054)`, `#2 doc_b:p1 (0.034)`
- Citations: -

### u3

- Question: What is the melting point of tungsten?
- Gold: None
- Predicted: I cannot answer from the provided documents.
- Issues: abstained, retrieval_miss
- Gold retrieval keys: ``
- Top retrieved: `#1 doc_b:p1 (-0.010)`, `#2 doc_a:p1 (-0.020)`
- Citations: -

### u4

- Question: What is the capital of Bhutan?
- Gold: None
- Predicted: I cannot answer from the provided documents.
- Issues: abstained, retrieval_miss
- Gold retrieval keys: ``
- Top retrieved: `#1 doc_a:p1 (0.000)`, `#2 doc_b:p1 (-0.020)`
- Citations: -

### u5

- Question: How many employees work at Siemens AG?
- Gold: None
- Predicted: I cannot answer from the provided documents.
- Issues: abstained, retrieval_miss
- Gold retrieval keys: ``
- Top retrieved: `#1 doc_a:p1 (0.107)`, `#2 doc_b:p1 (0.101)`
- Citations: -
