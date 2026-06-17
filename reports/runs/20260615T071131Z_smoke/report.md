# Eval Report — smoke

| Field | Value |
|-------|-------|
| Config | `configs/ci-smoke.yaml` |
| Tag | untagged |
| Generated | 2026-06-15T07:11:31.322082+00:00 |
| Items | 8 |
| Errors | 0 |

## Metric Snapshot

| Category | Metric | Value | Status |
|----------|--------|-------|--------|
| retrieval | recall@5 | 1.0000 | good |
| retrieval | mrr | 1.0000 | good |
| answer | exact_match | 0.0000 | needs work |
| answer | token_f1 | 0.0000 | needs work |
| grounding | citation_precision | 0.0000 | needs work |
| grounding | citation_recall | 0.0000 | needs work |
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
| token_f1 | 0.0000 |

## Grounding
| Metric | Value |
|--------|-------|
| citation_precision | 0.0000 |
| citation_recall | 0.0000 |

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
| index_build_ms | 3.8700 |
| avg_latency_ms / generation | 0.31 |
| avg_latency_ms / rerank | 0.00 |
| avg_latency_ms / retrieval | 0.10 |
| p95_latency_ms / generation | 0.73 |
| p95_latency_ms / rerank | 0.00 |
| p95_latency_ms / retrieval | 0.27 |
| avg_tokens / input | 0.00 |
| avg_tokens / output | 0.00 |
| total_cost_eur | 0.0000 |
| peak_memory_mb | 0.0000 |

## Per-Item Results

| id | type | retrieval | em | f1 | citation precision | issues |
|----|------|-----------|----|----|--------------------|--------|
| q1 | extractive | 1.0000 | 0.0000 | 0.0000 | 0.0000 | low_answer_f1 |
| q2 | extractive | 1.0000 | 0.0000 | 0.0000 | 0.0000 | low_answer_f1 |
| q3 | extractive | 1.0000 | 0.0000 | 0.0000 | 0.0000 | low_answer_f1 |
| q4 | extractive | 1.0000 | 0.0000 | 0.0000 | 0.0000 | low_answer_f1 |
| q5 | extractive | 1.0000 | 0.0000 | 0.0000 | 0.0000 | low_answer_f1 |
| q6 | extractive | 1.0000 | 0.0000 | 0.0000 | 0.0000 | low_answer_f1 |
| q7 | extractive | 1.0000 | 0.0000 | 0.0000 | 0.0000 | low_answer_f1 |
| q8 | extractive | 1.0000 | 0.0000 | 0.0000 | 0.0000 | low_answer_f1 |

## Per-Item Diagnostics

### q1

- Question: What are the products of photosynthesis?
- Gold: glucose and oxygen
- Predicted: [Gemini Error] API call failed: [Errno 8] nodename nor servname provided, or not known
- Issues: low_answer_f1
- Gold retrieval keys: `photosynthesis:p1`
- Top retrieved: `#1 photosynthesis:p1 (0.849)`, `#2 mitochondria:p1 (0.430)`, `#3 transformers:p1 (0.350)`
- Citations: -

### q2

- Question: Where do the light-dependent reactions occur?
- Gold: thylakoid membranes
- Predicted: [Gemini Error] API call failed: [Errno 8] nodename nor servname provided, or not known
- Issues: low_answer_f1
- Gold retrieval keys: `photosynthesis:p1`
- Top retrieved: `#1 photosynthesis:p1 (2.167)`, `#2 mitochondria:p1 (0.197)`, `#3 transformers:p1 (0.174)`
- Citations: -

### q3

- Question: What organelle produces most of the ATP in eukaryotic cells?
- Gold: mitochondria
- Predicted: [Gemini Error] API call failed: [Errno 8] nodename nor servname provided, or not known
- Issues: low_answer_f1
- Gold retrieval keys: `mitochondria:p1`
- Top retrieved: `#1 mitochondria:p1 (2.581)`, `#2 photosynthesis:p1 (0.559)`, `#3 transformers:p1 (0.350)`
- Citations: -

### q4

- Question: Who introduced the Transformer architecture?
- Gold: Vaswani et al.
- Predicted: [Gemini Error] API call failed: [Errno 8] nodename nor servname provided, or not known
- Issues: low_answer_f1
- Gold retrieval keys: `transformers:p1`
- Top retrieved: `#1 transformers:p1 (2.063)`, `#2 photosynthesis:p1 (0.199)`, `#3 mitochondria:p1 (0.197)`
- Citations: -

### q5

- Question: What paper introduced Transformers?
- Gold: Attention Is All You Need
- Predicted: [Gemini Error] API call failed: [Errno 8] nodename nor servname provided, or not known
- Issues: low_answer_f1
- Gold retrieval keys: `transformers:p1`
- Top retrieved: `#1 transformers:p1 (1.453)`
- Citations: -

### q6

- Question: What folds increase the surface area of the mitochondrial inner membrane?
- Gold: cristae
- Predicted: [Gemini Error] API call failed: [Errno 8] nodename nor servname provided, or not known
- Issues: low_answer_f1
- Gold retrieval keys: `mitochondria:p1`
- Top retrieved: `#1 mitochondria:p1 (4.290)`, `#2 photosynthesis:p1 (0.531)`, `#3 transformers:p1 (0.436)`
- Citations: -

### q7

- Question: What does the Calvin cycle produce?
- Gold: glyceraldehyde-3-phosphate
- Predicted: [Gemini Error] API call failed: [Errno 8] nodename nor servname provided, or not known
- Issues: low_answer_f1
- Gold retrieval keys: `photosynthesis:p1`
- Top retrieved: `#1 photosynthesis:p1 (1.701)`, `#2 mitochondria:p1 (0.390)`, `#3 transformers:p1 (0.174)`
- Citations: -

### q8

- Question: What technique replaces recurrence in Transformers?
- Gold: self-attention
- Predicted: [Gemini Error] API call failed: [Errno 8] nodename nor servname provided, or not known
- Issues: low_answer_f1
- Gold retrieval keys: `transformers:p1`
- Top retrieved: `#1 transformers:p1 (1.057)`, `#2 mitochondria:p1 (0.172)`, `#3 photosynthesis:p1 (0.133)`
- Citations: -
