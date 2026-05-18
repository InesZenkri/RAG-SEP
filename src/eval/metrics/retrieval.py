"""Category 1 - Retrieval quality.

Metrics: Recall@k, nDCG@k, MRR, Hit@k.

A retrieval is "correct" when any retrieved chunk's (doc_id, page) matches any
pair in the gold set for the item.
"""


from __future__ import annotations

import math

from rag.types import RetrievalResult

#Helper method to turn retrieved results into keys
def _make_key (result: RetrievalResult) -> str:
    return result.chunk.citation_key()


def recall_at_k(retrieved: list[RetrievalResult], gold_keys: set[str], k: int) -> float:

    if len(gold_keys) == 0:
        return 0.0

    matched_keys = set()

    for result in retrieved[:k]:
        key = _make_key(result)

        if key in gold_keys:
            matched_keys.add(key)  


    return len(matched_keys)  / len(gold_keys)    

def mrr(retrieved: list[RetrievalResult], gold_keys: set[str]) -> float:
    
    if len(gold_keys) == 0:
        return 0.0
    
    for index, result in enumerate(retrieved):
        rank = index + 1
        key = _make_key(result)

        if key in gold_keys:
            return 1 / rank

    return 0.0



def ndcg_at_k(retrieved: list[RetrievalResult], gold_keys: set[str], k: int) -> float:
    
    dcg = 0.0

    seen_keys = set()

    for index, result in enumerate(retrieved[:k]):
        rank = index + 1
        key = _make_key(result)

        if key in gold_keys and key not in seen_keys:
            relevance = 1
            seen_keys.add(key)
        else:
            relevance = 0
        
        dcg += relevance / math.log2(rank + 1)

    
    ideal_hits = min(len(gold_keys), k)
    ideal_dcg = 0.0

    for index in range(ideal_hits):
        rank = index + 1
        ideal_dcg += 1 / math.log2(rank + 1)

    if ideal_dcg == 0:
        return 0.0
    
    return dcg / ideal_dcg



def hit_at_k(retrieved: list[RetrievalResult], gold_keys: set[str], k: int) -> float:
    
    if len(gold_keys) == 0:
        return 0.0
    
    for result in retrieved[:k]:
        key = _make_key(result)
        if key in gold_keys:
            return 1.0
        
    return 0.0



