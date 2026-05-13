"""Category 4 - Abstention behaviour.

- false_refusal_rate: fraction of answerable items the system refused.
- false_answer_rate:  fraction of unanswerable items the system answered.
- precision_coverage_curve: thresholded coverage vs. answer precision, used
  to pick the abstention threshold in the final report.
"""

from __future__ import annotations

from eval.dataset import EvalItem

from rag.types import Answer


def false_refusal_rate(pairs: list[tuple[EvalItem, Answer]]) -> float:
    """Calculates the fraction of answerable items the system incorrectly refused."""
    answerable_items = []
    for pair in pairs:
        if pair[0].answer or pair[0].expected_answers:
            answerable_items.append(pair)
            
    if not answerable_items:
        return 0.0
        
    total_answerable = len(answerable_items)
    refusals = 0
    for item, prediction in answerable_items:
        if prediction.abstained:
            refusals += 1
            
    return refusals / total_answerable

def false_answer_rate(pairs: list[tuple[EvalItem, Answer]]) -> float:
    """Determines the fraction of unanswerable items the system attempted to answer."""
    unanswerable_items = []
    for pair in pairs:
        if not (pair[0].answer or pair[0].expected_answers):
            unanswerable_items.append(pair)
            
    if not unanswerable_items:
        return 0.0
        
    total_unanswerable = len(unanswerable_items)
    false_answers = 0
    for item, prediction in unanswerable_items:
        if not prediction.abstained:
            false_answers += 1
            
    return false_answers / total_unanswerable

def precision_coverage_curve(pairs: list[tuple[EvalItem, Answer]]) -> list[tuple[float, float, float]]:
    """Maps thresholded coverage against answer precision to determine the optimal abstention threshold for the final report."""
    if not pairs:
        return []
        
    unique_confidences = set()
    for ref, prediction in pairs:
        unique_confidences.add(prediction.confidence)
        
    thresholds = sorted(list(unique_confidences))
    results = []
    total_pairs = len(pairs)
    
    for threshold in thresholds:
        covered = []
        for pair in pairs:
            if pair[1].confidence >= threshold:
                covered.append(pair)
        
        if not covered:
            continue
            
        total_covered = len(covered)
        attempts = []
        for pair in covered:
            if not pair[1].abstained:
                attempts.append(pair)
                
        if not attempts:
            results.append((threshold, total_covered / total_pairs, 0.0))
            continue
            
        total_attempts = len(attempts)
        correct = 0
        for item, prediction in attempts:
            is_exact = item.answer and prediction.text == item.answer
            is_expected = item.expected_answers and (prediction.text in item.expected_answers)
            
            if is_exact or is_expected:
                correct += 1
                
        results.append((threshold, total_covered / total_pairs, correct / total_attempts))
        
    return results