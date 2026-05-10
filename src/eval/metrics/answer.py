"""Category 2 - Answer quality.

For extractive questions: normalised Exact-Match and token-level F1
(SQuAD-style normalisation: lowercase, strip punctuation/articles, collapse
whitespace).

For abstractive / long-form questions: delegated to
``eval.judge.LLMJudge.score_answer`` using a different model family than the
generator to reduce bias.
"""

from __future__ import annotations
import re 
import string
from collections import Counter


def normalize(text: str) -> str:
    """Lowers text and remove punctuation, articles and extra whitespace."""
    def lower(text: str) -> str:
        return text.lower()

    def remove_punc(text: str) -> str:
        exclude = set(string.punctuation)
        return "".join(ch for ch in text if ch not in exclude)

    def remove_articles(text):
        return re.sub(r'\b(a|an|the)\b', ' ', text)

    def white_space_fix(text: str) -> str:
        return " ".join(text.split())

    return white_space_fix(remove_articles(remove_punc(lower(text))))


def exact_match(prediction: str, references: list[str]) -> float:
    """checks if the normalized prediction exactly matches the normalized ground-truth answer"""
    norm_pred = normalize(prediction)
    for ref in references:
        if norm_pred == normalize(ref):
            return 1.0
    return 0.0


def token_f1(prediction: str, references: list[str]) -> float:
    """measures overlap between prediction and ground-truth tokens."""
    pred_tokens = normalize(prediction).split()
    
    if not references:
        return 0.0
    
    f1_scores = []
    for ref in references:
        ref_tokens = normalize(ref).split()
        
        if not pred_tokens or not ref_tokens:
            f1_scores.append(1.0 if pred_tokens == ref_tokens else 0.0)
            continue
            
        common = Counter(pred_tokens) & Counter(ref_tokens)
        num_same = sum(common.values())
        
        if num_same == 0:
            f1_scores.append(0.0)
            continue
            
        precision = 1.0 * num_same / len(pred_tokens)
        recall = 1.0 * num_same / len(ref_tokens)
        f1 = (2 * precision * recall) / (precision + recall)
        f1_scores.append(f1)
        
    return max(f1_scores)