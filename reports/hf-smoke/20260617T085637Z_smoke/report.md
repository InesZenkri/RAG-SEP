# Eval Report — smoke

| Field | Value |
|-------|-------|
| Config | `configs/baseline.yaml` |
| Tag | hf-progress-test |
| Generated | 2026-06-17T08:56:46.718548+00:00 |
| Items | 8 |
| Errors | 0 |

## Metric Snapshot

| Category | Metric | Value | Status |
|----------|--------|-------|--------|
| retrieval | recall@5 | 1.0000 | good |
| retrieval | mrr | 1.0000 | good |
| answer | exact_match | 0.0000 | needs work |
| answer | token_f1 | 0.3142 | needs work |
| grounding | citation_precision | 0.7500 | ok |
| grounding | citation_recall | 0.7500 | ok |
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
| token_f1 | 0.3142 |

## Grounding
| Metric | Value |
|--------|-------|
| citation_precision | 0.7500 |
| citation_recall | 0.7500 |

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
| index_build_ms | 9064.6400 |
| avg_latency_ms / generation | 0.41 |
| avg_latency_ms / rerank | 0.00 |
| avg_latency_ms / retrieval | 28.35 |
| p95_latency_ms / generation | 0.66 |
| p95_latency_ms / rerank | 0.00 |
| p95_latency_ms / retrieval | 48.31 |
| avg_tokens / input | 467.50 |
| avg_tokens / output | 19.90 |
| total_cost_eur | 0.0000 |
| peak_memory_mb | 0.0000 |

## Per-Item Results

| id | type | retrieval | em | f1 | citation precision | issues |
|----|------|-----------|----|----|--------------------|--------|
| q1 | extractive | 1.0000 | 0.0000 | 0.5455 | 1.0000 | none |
| q2 | extractive | 1.0000 | 0.0000 | 0.5714 | 1.0000 | none |
| q3 | extractive | 1.0000 | 0.0000 | 0.1818 | 1.0000 | low_answer_f1 |
| q4 | extractive | 1.0000 | 0.0000 | 0.5000 | 0.0000 | unsupported_citation |
| q5 | extractive | 1.0000 | 0.0000 | 0.4545 | 1.0000 | low_answer_f1 |
| q6 | extractive | 1.0000 | 0.0000 | 0.1429 | 1.0000 | low_answer_f1 |
| q7 | extractive | 1.0000 | 0.0000 | 0.0000 | 0.0000 | low_answer_f1 |
| q8 | extractive | 1.0000 | 0.0000 | 0.1176 | 1.0000 | low_answer_f1 |

## Per-Item Diagnostics

### q3

- Question: What organelle produces most of the ATP in eukaryotic cells?
- Gold: mitochondria
- Predicted: Mitochondria produce most of the cell's ATP through cellular respiration [mitochondria:p1].
- Issues: low_answer_f1
- Gold retrieval keys: `mitochondria:p1`
- Top retrieved: `#1 mitochondria:p1 (0.680)`, `#2 photosynthesis:p1 (0.371)`, `#3 transformers:p1 (0.004)`
- Citations: `mitochondria:p1` (valid)

### q4

- Question: Who introduced the Transformer architecture?
- Gold: Vaswani et al.
- Predicted: The Transformer architecture was introduced by Vaswani et al. [transformers:p1].
- Issues: unsupported_citation
- Gold retrieval keys: `transformers:p1`
- Top retrieved: `#1 transformers:p1 (0.444)`, `#2 mitochondria:p1 (0.046)`, `#3 photosynthesis:p1 (-0.001)`
- Citations: `transformers:p1` (valid)

### q5

- Question: What paper introduced Transformers?
- Gold: Attention Is All You Need
- Predicted: The Transformer was introduced by Vaswani et et al. in the 2017 paper "Attention Is All You Need" [transformers:p1].
- Issues: low_answer_f1
- Gold retrieval keys: `transformers:p1`
- Top retrieved: `#1 transformers:p1 (0.323)`, `#2 photosynthesis:p1 (0.090)`, `#3 mitochondria:p1 (0.064)`
- Citations: `transformers:p1` (valid)

### q6

- Question: What folds increase the surface area of the mitochondrial inner membrane?
- Gold: cristae
- Predicted: The folds that increase the surface area of the mitochondrial inner membrane are called cristae [mitochondria:p1].
- Issues: low_answer_f1
- Gold retrieval keys: `mitochondria:p1`
- Top retrieved: `#1 mitochondria:p1 (0.588)`, `#2 photosynthesis:p1 (0.250)`, `#3 transformers:p1 (0.046)`
- Citations: `mitochondria:p1` (valid)

### q7

- Question: What does the Calvin cycle produce?
- Gold: glyceraldehyde-3-phosphate
- Predicted: [Gemini Error] API call failed: 429 RESOURCE_EXHAUSTED. {'error': {'code': 429, 'message': 'You exceeded your current quota, please check your plan and billing details. For more information on this error, head to: https://ai.google.dev/gemini-api/docs/rate-limits. To monitor your current usage, head to: https://ai.dev/rate-limit. \n* Quota exceeded for metric: generativelanguage.googleapis.com/generate_content_free_tier_requests, limit: 5, model: gemini-2.5-flash\nPlease retry in 36.047266938s.', 'status': 'RESOURCE_EXHAUSTED', 'details': [{'@type': 'type.googleapis.com/google.rpc.Help', 'links': [{'description': 'Learn more about Gemini API quotas', 'url': 'https://ai.google.dev/gemini-api/docs/rate-limits'}]}, {'@type': 'type.googleapis.com/google.rpc.QuotaFailure', 'violations': [{'quotaMetric': 'generativelanguage.googleapis.com/generate_content_free_tier_requests', 'quotaId': 'GenerateRequestsPerMinutePerProjectPerModel-FreeTier', 'quotaDimensions': {'location': 'global', 'model': 'gemini-2.5-flash'}, 'quotaValue': '5'}]}, {'@type': 'type.googleapis.com/google.rpc.RetryInfo', 'retryDelay': '36s'}]}}
- Issues: low_answer_f1
- Gold retrieval keys: `photosynthesis:p1`
- Top retrieved: `#1 photosynthesis:p1 (0.649)`, `#2 mitochondria:p1 (0.331)`, `#3 transformers:p1 (0.038)`
- Citations: -

### q8

- Question: What technique replaces recurrence in Transformers?
- Gold: self-attention
- Predicted: The Transformer replaces recurrence and convolutions with self-attention to model dependencies between input and output tokens [transformers:p1].
- Issues: low_answer_f1
- Gold retrieval keys: `transformers:p1`
- Top retrieved: `#1 transformers:p1 (0.463)`, `#2 photosynthesis:p1 (0.174)`, `#3 mitochondria:p1 (0.131)`
- Citations: `transformers:p1` (valid)
