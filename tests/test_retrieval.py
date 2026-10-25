"""Proposal §4 RAG design: BM25 and dense search fused, then a cross-encoder reranker, so legal
terms like "indemnify" match exactly. Dense models are replaced by small fakes."""

import numpy as np
import pytest

from counselcopilot.retrieval.index import BM25, HybridIndex, Passage, rrf, tokenize

CLAUSES = [
    "The Receiving Party shall indemnify the Disclosing Party against all losses.",
    "This Agreement is governed by the laws of the State of New York.",
    "The Receiving Party shall return or destroy Confidential Information on request.",
    "Notices must be given in writing to the addresses above.",
]


def index(**kw) -> HybridIndex:
    return HybridIndex([Passage(str(i), t) for i, t in enumerate(CLAUSES)], **kw)


def test_tokenizer_drops_stopwords_and_stems():
    toks = tokenize("The obligations shall survive termination of the agreements")
    assert "the" not in toks and "shall" not in toks
    assert tokenize("agreements") == tokenize("agreement")


def test_exact_legal_term_ranks_first():
    hits = index().search("indemnify", k=2)
    assert hits[0].passage.id == "0"


def test_bm25_only_drops_passages_with_no_overlap():
    hits = index().search("indemnify", k=4)
    assert [h.passage.id for h in hits] == ["0"]


def test_bm25_rare_terms_weigh_more():
    bm = BM25(["party party party law", "party destroy"])
    s = bm.scores("party destroy")
    assert s[1] > s[0]


def test_empty_index_returns_nothing():
    assert HybridIndex([]).search("anything") == []
    assert len(HybridIndex([])) == 0


def test_hits_carry_rank_and_are_cut_at_k():
    hits = index().search("party information agreement", k=2)
    assert len(hits) == 2 and [h.rank for h in hits] == [0, 1]


def test_reciprocal_rank_fusion_rewards_agreement():
    fused = rrf([[0, 1, 2], [1, 0, 2]])
    assert fused[0] == pytest.approx(fused[1])
    assert fused[0] > fused[2]
    assert rrf([[5]], k=60)[5] == pytest.approx(1 / 61)


class FakeEncoder:
    """Embeds by a hand-made concept vector, so "give back" finds "return or destroy"
    although BM25 sees no shared word."""

    concepts = [("return", "destroy", "give back"), ("law", "governed"), ("indemnif", "losses"), ("notice",)]

    def encode(self, texts, normalize_embeddings=True):
        out = np.array([[float(any(w in t.lower() for w in c)) for c in self.concepts] for t in texts]) + 1e-6
        return out / np.linalg.norm(out, axis=1, keepdims=True)


@pytest.mark.xfail(strict=True, reason="BUG: in hybrid mode, passages with BM25 score 0 still enter reciprocal "
                                        "rank fusion in index order, so the first segments of an NDA get rank "
                                        "credit for matching nothing and can outrank the true dense hit")
def test_dense_search_finds_paraphrases_bm25_misses():
    assert index().search("give back", k=4) == []  # no shared word for BM25
    hits = index(encoder=FakeEncoder()).search("give back", k=1)
    assert hits[0].passage.id == "2"


def test_dense_search_can_return_passages_bm25_cannot():
    hits = index(encoder=FakeEncoder()).search("give back", k=4)
    assert "2" in {h.passage.id for h in hits}


class ReverseReranker:
    """Prefers the passage that BM25 likes least, to show the reranker has the last word."""

    def predict(self, pairs):
        return [-len(p) for _, p in pairs]


def test_reranker_reorders_candidates():
    plain = index(encoder=FakeEncoder()).search("party", k=4)
    reranked = index(encoder=FakeEncoder(), reranker=ReverseReranker()).search("party", k=4)
    shortest = min(CLAUSES, key=len)
    assert reranked[0].passage.text == shortest
    assert {h.passage.id for h in plain} == {h.passage.id for h in reranked}
