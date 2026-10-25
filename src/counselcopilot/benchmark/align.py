"""Match compiled requirement cards to a pack's gold rules, so RQ1 can be scored on compiled cards
and the compiler gets its own precision and recall (design D17).

The gold pack's prose was written from its rules, and every rule carries the verbatim quote it was
written into. A card matches the gold rule whose quote it shares most (same document, word overlap
of the two quotes), provided the overlap is high enough and the kinds are compatible. Several cards
can match one gold rule (the compiler split or repeated it); their findings are merged under the
gold id. A card that matches nothing keeps its own id, so its findings count as false alarms.
"""

from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass, field

from ..policy.schema import PolicyPack, Rule
from ..review.findings import Finding

MIN_OVERLAP = 0.5


def _words(s: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", s.lower()))


def overlap(a: str, b: str) -> float:
    """Share of the shorter quote's words that are in the other quote."""
    wa, wb = _words(a), _words(b)
    return len(wa & wb) / max(1, min(len(wa), len(wb)))


def _compatible(card: Rule, gold: Rule) -> bool:
    if card.kind == "field" or gold.kind == "field":
        return card.kind == gold.kind and card.constraint.field == gold.constraint.field
    return True  # require/forbid can be phrased either way round ("must not share" vs "share only if")


def _quote(r: Rule) -> tuple[str, str]:
    return ((r.source.document if r.source else "").strip().lower(), r.source.quote if r.source else "")


@dataclass
class Alignment:
    card_to_gold: dict[str, str | None]
    scores: dict[str, float] = field(default_factory=dict)

    def gold_covered(self) -> set[str]:
        return {g for g in self.card_to_gold.values() if g}

    def report(self, gold: PolicyPack) -> dict:
        n_cards, n_gold = len(self.card_to_gold), len(gold.rules)
        matched = sum(g is not None for g in self.card_to_gold.values())
        covered = self.gold_covered()
        per_gold = defaultdict(int)
        for g in self.card_to_gold.values():
            if g:
                per_gold[g] += 1
        return {
            "cards": n_cards, "gold_rules": n_gold,
            "precision": round(matched / n_cards, 3) if n_cards else 0.0,  # cards that are a real rule
            "recall": round(len(covered) / n_gold, 3) if n_gold else 0.0,  # gold rules the compiler found
            "missed_gold": sorted(r.id for r in gold.rules if r.id not in covered),
            "unmatched_cards": sorted(c for c, g in self.card_to_gold.items() if g is None),
            "split_rules": {g: n for g, n in sorted(per_gold.items()) if n > 1},
        }


def align(cards: PolicyPack, gold: PolicyPack, min_overlap: float = MIN_OVERLAP) -> Alignment:
    out: dict[str, str | None] = {}
    scores: dict[str, float] = {}
    for c in cards.rules:
        cdoc, cq = _quote(c)
        best, best_s = None, 0.0
        for g in gold.rules:
            gdoc, gq = _quote(g)
            if not gq or not _compatible(c, g) or (cdoc and gdoc and cdoc != gdoc):
                continue
            s = overlap(cq, gq)
            if s > best_s:
                best, best_s = g.id, s
        out[c.id] = best if best_s >= min_overlap else None
        scores[c.id] = round(best_s, 3)
    return Alignment(out, scores)


def remap_findings(findings: list[Finding], alignment: Alignment) -> list[Finding]:
    """Findings on cards -> findings on gold rule ids; duplicates (split cards) keep the most confident."""
    best: dict[tuple[str, str], Finding] = {}
    for f in findings:
        rid = alignment.card_to_gold.get(f.rule_id) or f.rule_id
        g = f.model_copy(update={"rule_id": rid})
        k = (rid, g.type.value)
        if k not in best or g.confidence > best[k].confidence:
            best[k] = g
    return list(best.values())
