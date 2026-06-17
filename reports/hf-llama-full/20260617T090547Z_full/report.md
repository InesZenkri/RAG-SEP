# Eval Report — full

| Field | Value |
|-------|-------|
| Config | `configs/baseline.yaml` |
| Tag | hf-llama-full-test |
| Generated | 2026-06-17T09:06:05.519344+00:00 |
| Items | 10 |
| Errors | 0 |

## Metric Snapshot

| Category | Metric | Value | Status |
|----------|--------|-------|--------|
| retrieval | recall@5 | 1.0000 | good |
| retrieval | mrr | 1.0000 | good |
| answer | exact_match | 0.0000 | needs work |
| answer | token_f1 | 0.3114 | needs work |
| grounding | citation_precision | 0.0000 | needs work |
| grounding | citation_recall | 0.0000 | needs work |
| abstention | false_refusal_rate | 0.1000 | good |
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
| token_f1 | 0.3114 |

## Grounding
| Metric | Value |
|--------|-------|
| citation_precision | 0.0000 |
| citation_recall | 0.0000 |

## Abstention
| Metric | Value |
|--------|-------|
| false_refusal_rate | 0.1000 |
| false_answer_rate | 0.0000 |

## Robustness
| Metric | Value |
|--------|-------|
| status | not_implemented |

## Efficiency
| Metric | Value |
|--------|-------|
| num_queries | 10 |
| index_build_ms | 8756.3200 |
| avg_latency_ms / generation | 856.91 |
| avg_latency_ms / rerank | 0.00 |
| avg_latency_ms / retrieval | 51.93 |
| p95_latency_ms / generation | 1789.56 |
| p95_latency_ms / rerank | 0.00 |
| p95_latency_ms / retrieval | 67.48 |
| avg_tokens / input | 1011.00 |
| avg_tokens / output | 36.70 |
| total_cost_eur | 0.0000 |
| peak_memory_mb | 0.0000 |

## Per-Item Results

| id | type | retrieval | em | f1 | citation precision | issues |
|----|------|-----------|----|----|--------------------|--------|
| 852703f0-8373-43a2-a18a-eb5908ad0779 | abstractive | 1.0000 | 0.0000 | 0.2391 | 0.0000 | low_answer_f1 |
| d639debd-b486-4fd2-a555-45f39a35cedf | abstractive | 1.0000 | 0.0000 | 0.3889 | 0.0000 | low_answer_f1 |
| 2d25d3ca-2ecb-44c1-adc9-e090bb187824 | abstractive | 1.0000 | 0.0000 | 0.4242 | 0.0000 | low_answer_f1 |
| ad04523d-ab6c-414d-9c58-5ed28d2fbe86 | abstractive | 1.0000 | 0.0000 | 0.5600 | 0.0000 | none |
| 54794ee1-92d1-4e56-865a-224dda2788ae | extractive | 1.0000 | 0.0000 | 0.0000 | 0.0000 | abstained, low_answer_f1 |
| 8f2f108d-8edf-4111-81aa-8dc5bf8211a2 | extractive | 1.0000 | 0.0000 | 0.2963 | 0.0000 | low_answer_f1 |
| 3bdbc190-4695-4fc4-9255-41ed3ba45ce5 | extractive | 1.0000 | 0.0000 | 0.5128 | 0.0000 | none |
| ddf9dfa2-8a4b-4bee-89a1-5578336eb5a8 | abstractive | 1.0000 | 0.0000 | 0.0769 | 0.0000 | low_answer_f1 |
| aa895a0e-1ba6-4d08-924a-7729247ed24d | abstractive | 1.0000 | 0.0000 | 0.3607 | 0.0000 | low_answer_f1 |
| 87856189-29a8-4104-a8e1-c0af6a849833 | abstractive | 1.0000 | 0.0000 | 0.2545 | 0.0000 | low_answer_f1 |

## Per-Item Diagnostics

### 852703f0-8373-43a2-a18a-eb5908ad0779

- Question: What are the challenges in estimating output impedance in inverter-based grids?
- Gold: Estimating output impedance in inverter-based grids is challenging due to dynamic grid conditions, which require real-time estimation. Traditional methods like signal injection and historical data analysis have limitations, such as sensitivity to noise and complexity.
- Predicted: The main challenges in accurately estimating output line impedance stem from several factors, including: (i) lack of access to global measurements or networkwide data, (ii) measured signals often lack the necessary persistence of excitation, (iii) only local output voltage and current are measurable, and (iv) altering the power system to assist in impedance estimation is either impractical or not allowed.
- Issues: low_answer_f1
- Gold retrieval keys: `2410.14077v2:p1`
- Top retrieved: `#1 2410.14077v2:p1 (0.822)`, `#2 2410.14077v2:p1 (0.746)`, `#3 2410.14077v2:p1 (0.734)`
- Citations: -

### d639debd-b486-4fd2-a555-45f39a35cedf

- Question: How does discarding q-axis dynamics affect noise reduction in power networks?
- Gold: Discarding q-axis dynamics improves noise rejection, resulting in lower RMSPE values for resistance and inductance when only d-axis dynamics are used, enhancing estimation accuracy.
- Predicted: Discarding q-axis dynamics allows for effective rejection of noise in power networks.
- Issues: low_answer_f1
- Gold retrieval keys: `2410.14077v2:p1`
- Top retrieved: `#1 2410.14077v2:p1 (0.495)`, `#2 2410.14077v2:p1 (0.474)`, `#3 2410.14077v2:p1 (0.458)`
- Citations: -

### 2d25d3ca-2ecb-44c1-adc9-e090bb187824

- Question: What is the purpose of using a variable direction forgetting recursive-least-square algorithm in power networks?
- Gold: The variable direction forgetting recursive-least-square (VDF-RLS) algorithm is used in power networks to improve the estimation of inverter output impedance. It adapts effectively to changes and maintains stable estimation under no-excitation conditions, outperforming other algorithms like RLS without forgetting and Kalman filter-based methods.
- Predicted: The purpose of using a variable direction forgetting recursive-least-square algorithm in power networks is to address the issue of non-persistent excitation and to enhance the algorithm's robustness against noise.
- Issues: low_answer_f1
- Gold retrieval keys: `2410.14077v2:p1`
- Top retrieved: `#1 2410.14077v2:p1 (0.605)`, `#2 2410.14077v2:p1 (0.558)`, `#3 2410.14077v2:p1 (0.439)`
- Citations: -

### 54794ee1-92d1-4e56-865a-224dda2788ae

- Question: Is the inverter connected to a grid with a voltage of 480 V?
- Gold: Yes.
- Predicted: I cannot answer from the provided documents.
- Issues: abstained, low_answer_f1
- Gold retrieval keys: `2410.14077v2:p1`
- Top retrieved: `#1 2410.14077v2:p1 (0.460)`, `#2 2410.14077v2:p1 (0.452)`, `#3 2410.14077v2:p1 (0.446)`
- Citations: -

### 8f2f108d-8edf-4111-81aa-8dc5bf8211a2

- Question: Does the VDF-RLS algorithm maintain stable resistance estimation after excitation ceases?
- Gold: Yes, the VDF-RLS algorithm maintains stable resistance estimation after excitation ceases.
- Predicted: The VDF-RLS algorithm demonstrates superior performance in adapting to impedance changes and maintaining stable estimation under no-excitation conditions.
- Issues: low_answer_f1
- Gold retrieval keys: `2410.14077v2:p1`
- Top retrieved: `#1 2410.14077v2:p1 (0.681)`, `#2 2410.14077v2:p1 (0.532)`, `#3 2410.14077v2:p1 (0.527)`
- Citations: -

### ddf9dfa2-8a4b-4bee-89a1-5578336eb5a8

- Question: How does the VDF-RLS algorithm maintain stability in the absence of persistent excitation?
- Gold: It maintains stability like the RLS algorithm without forgetting.
- Predicted: The VDF-RLS algorithm demonstrates superior performance in both adapting to impedance changes and maintaining stable estimation under no-excitation conditions.
- Issues: low_answer_f1
- Gold retrieval keys: `2410.14077v2:p1`
- Top retrieved: `#1 2410.14077v2:p1 (0.577)`, `#2 2410.14077v2:p1 (0.533)`, `#3 2410.14077v2:p1 (0.520)`
- Citations: -

### aa895a0e-1ba6-4d08-924a-7729247ed24d

- Question: How do different estimation algorithms perform under no-excitation conditions in power networks?
- Gold: Under no-excitation conditions, the VDF-RLS algorithm maintains accuracy better than others. The Kalman filter and CF-RLS become highly sensitive to measurement noise, resulting in significantly higher RMSPE values compared to VDF-RLS. RLS without forgetting fails to adapt well.
- Predicted: The VDF-RLS method achieves more than three times lower error compared to existing approaches such as constant forgetting RLS and the Kalman filter, particularly in low-excitation conditions.
- Issues: low_answer_f1
- Gold retrieval keys: `2410.14077v2:p1`
- Top retrieved: `#1 2410.14077v2:p1 (0.517)`, `#2 2410.14077v2:p1 (0.496)`, `#3 2410.14077v2:p1 (0.486)`
- Citations: -

### 87856189-29a8-4104-a8e1-c0af6a849833

- Question: How do existing methods like signal injection compare with newer approaches for estimating line impedance?
- Gold: Existing methods like signal injection often face limitations such as high sensitivity to noise and complexity. Newer approaches aim to address these issues by improving accuracy and adaptability through advanced algorithms like VDF-RLS.
- Predicted: Existing methods like signal injection, as described in [6], can distort the output voltage and tamper with power flow, which is not allowed.
- Issues: low_answer_f1
- Gold retrieval keys: `2410.14077v2:p1`
- Top retrieved: `#1 2410.14077v2:p1 (0.652)`, `#2 2410.14077v2:p1 (0.602)`, `#3 2410.14077v2:p1 (0.593)`
- Citations: -
