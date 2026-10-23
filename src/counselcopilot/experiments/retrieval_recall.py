"""How often the gold evidence span is among the top-k retrieved segments (review problem 11).
A clause that is not retrieved looks absent, so this caps omission precision. No LLM needed."""

from __future__ import annotations

import numpy as np

from ..data.contractnli import ContractNLI
from ..retrieval.index import HybridIndex, Passage, load_encoder, load_reranker


def retrieval_recall(data: ContractNLI, split: str = "dev", ks=(5, 8, 12, 20), dense: str | None = None,
                     rerank: str | None = None, neighbours: int = 0) -> dict:
    enc = load_encoder(dense) if dense else None
    rr = load_reranker(rerank) if rerank else None
    hits = {k: [] for k in ks}
    per_h = {k: {} for k in ks}
    for doc in data[split]:
        idx = HybridIndex([Passage(str(i), s) for i, s in enumerate(doc.span_texts)], enc, rr)
        for h in data.hypothesis_keys:
            gold = set(doc.annotations[h].spans)
            if not gold:
                continue
            ranked = [int(x.passage.id) for x in idx.search(data.hypotheses[h].text, k=max(ks), candidates=max(30, max(ks)))]
            for k in ks:
                got = set(ranked[:k])
                for d in range(1, neighbours + 1):
                    got |= {i + d for i in got} | {i - d for i in got}
                ok = bool(got & gold)
                hits[k].append(ok)
                per_h[k].setdefault(h, []).append(ok)
    return {
        "split": split, "dense": dense, "rerank": rerank, "neighbours": neighbours,
        "recall_at_k": {k: round(float(np.mean(v)), 4) for k, v in hits.items()},
        "worst_hypotheses_at_k": {k: sorted(((h, round(float(np.mean(v)), 3)) for h, v in per_h[k].items()),
                                             key=lambda x: x[1])[:4] for k in ks},
    }
