"""Hybrid retrieval: BM25 + optional dense embeddings, fused with reciprocal rank fusion,
plus an optional cross-encoder reranker (design §4, R5).

The same index class is used in both directions of two-way retrieval:
- forward: NDA clause -> rules  (index over rules)
- reverse: applicable rule -> NDA spans  (index over the NDA's spans)

BM25 has no dependencies. Dense retrieval and reranking need `pip install -e '.[dense]'`
and are switched on by passing an encoder / reranker.
"""

from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass, field
from typing import Any, Protocol, Sequence

import numpy as np

_TOKEN = re.compile(r"[a-z0-9]+(?:'[a-z]+)?")
STOPWORDS = frozenset(
    "a an the of to in on for by with and or is are be been being as at from that this these those "
    "it its any all such shall will may which who whom whose under upon into than other".split()
)
_SUFFIXES = ("ations", "ation", "ments", "ment", "ities", "ity", "ings", "ing", "ies", "ed", "es", "s")


def _stem(w: str) -> str:
    for suf in _SUFFIXES:
        if len(w) > len(suf) + 3 and w.endswith(suf):
            return w[: -len(suf)]
    return w


def tokenize(text: str) -> list[str]:
    return [_stem(t) for t in _TOKEN.findall(text.lower()) if t not in STOPWORDS]


@dataclass(frozen=True)
class Passage:
    id: str
    text: str
    meta: dict[str, Any] = field(default_factory=dict, hash=False, compare=False)


@dataclass(frozen=True)
class Hit:
    passage: Passage
    score: float
    rank: int


class BM25:
    def __init__(self, docs: Sequence[str], k1: float = 1.5, b: float = 0.75):
        self.k1, self.b = k1, b
        self.toks = [tokenize(d) for d in docs]
        self.tf = [Counter(t) for t in self.toks]
        self.len = np.array([len(t) for t in self.toks], dtype=float)
        self.avg = float(self.len.mean()) if len(self.len) else 0.0
        df: Counter = Counter()
        for t in self.toks:
            df.update(set(t))
        n = len(docs)
        self.idf = {w: math.log(1 + (n - c + 0.5) / (c + 0.5)) for w, c in df.items()}

    def scores(self, query: str) -> np.ndarray:
        q = tokenize(query)
        out = np.zeros(len(self.toks))
        for i, tf in enumerate(self.tf):
            norm = self.k1 * (1 - self.b + self.b * self.len[i] / (self.avg or 1))
            s = 0.0
            for w in q:
                f = tf.get(w)
                if f:
                    s += self.idf[w] * f * (self.k1 + 1) / (f + norm)
            out[i] = s
        return out


class Encoder(Protocol):
    def encode(self, texts: list[str], normalize_embeddings: bool = True) -> np.ndarray: ...


class Reranker(Protocol):
    def predict(self, pairs: list[tuple[str, str]]) -> Sequence[float]: ...


def load_encoder(name: str = "BAAI/bge-small-en-v1.5") -> Encoder:  # pragma: no cover
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(name)


def load_reranker(name: str = "BAAI/bge-reranker-base") -> Reranker:  # pragma: no cover
    from sentence_transformers import CrossEncoder

    return CrossEncoder(name)


def rrf(rankings: list[list[int]], k: int = 60) -> dict[int, float]:
    """Reciprocal rank fusion of several rankings (lists of item indices, best first)."""
    fused: dict[int, float] = {}
    for ranking in rankings:
        for r, idx in enumerate(ranking):
            fused[idx] = fused.get(idx, 0.0) + 1.0 / (k + r + 1)
    return fused


class HybridIndex:
    def __init__(self, passages: Sequence[Passage], encoder: Encoder | None = None,
                 reranker: Reranker | None = None):
        self.passages = list(passages)
        self.bm25 = BM25([p.text for p in self.passages])
        self.encoder = encoder
        self.reranker = reranker
        self.emb = (encoder.encode([p.text for p in self.passages], normalize_embeddings=True)
                    if encoder is not None and self.passages else None)

    def __len__(self) -> int:
        return len(self.passages)

    def search(self, query: str, k: int = 5, candidates: int = 30) -> list[Hit]:
        if not self.passages:
            return []
        bm = self.bm25.scores(query)
        rankings = [list(np.argsort(-bm)[:candidates])]
        if self.emb is not None:
            qv = self.encoder.encode([query], normalize_embeddings=True)[0]
            dense = self.emb @ qv
            rankings.append(list(np.argsort(-dense)[:candidates]))
            fused = rrf(rankings)
        else:  # BM25 only: keep BM25 scores, drop zero-score passages
            fused = {int(i): float(bm[i]) for i in rankings[0] if bm[i] > 0}
        order = sorted(fused, key=fused.get, reverse=True)[:candidates]
        if self.reranker is not None and order:
            rs = self.reranker.predict([(query, self.passages[i].text) for i in order])
            pairs = sorted(zip(order, rs), key=lambda x: -x[1])
            order, scores = [i for i, _ in pairs], [float(s) for _, s in pairs]
        else:
            scores = [fused[i] for i in order]
        return [Hit(self.passages[i], s, r) for r, (i, s) in enumerate(zip(order[:k], scores[:k]))]
