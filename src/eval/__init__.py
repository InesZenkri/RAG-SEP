"""Evaluation harness covering all six required metric categories:

1. Retrieval quality   -> eval/metrics/retrieval.py
2. Answer quality      -> eval/metrics/answer.py
3. Grounding/citation  -> eval/metrics/grounding.py
4. Abstention          -> eval/metrics/abstention.py
5. Robustness          -> eval/metrics/robustness.py
6. Efficiency          -> eval/metrics/efficiency.py
"""

from eval.dataset import EvalItem, load_jsonl, load_suite

__all__ = ["EvalItem", "load_jsonl", "load_suite"]
