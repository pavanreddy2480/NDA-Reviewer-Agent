"""Precedent memory (design §3.1, §4 T7): deviations a senior lawyer has already approved.

"Singapore law accepted for vendors, approved by the General Counsel on 3 Oct" is stored once and
reused, so the same question is not escalated twice and the knowledge stays when a consultant
leaves. Lookup is by rule id and counterparty (a named counterparty first, then the counterparty
type), optionally by the deviating value, with BM25 over the notes as a fallback for free-text
queries. Stored as JSON so it survives between sessions.

For evaluation the memory is pre-filled with ~30 scripted approvals (`scripted_precedents`,
proposal §5 agentic metric: escalations avoided by memory at equal accuracy).
"""

from __future__ import annotations

import json
import random
from dataclasses import asdict, dataclass, field
from pathlib import Path

from ..policy.schema import CounterpartyType, PolicyPack
from ..retrieval.index import HybridIndex, Passage


@dataclass
class Precedent:
    rule_id: str
    counterparty: str  # counterparty type ("vendor") or a counterparty name
    approved_by: str
    value: str = ""  # the deviating value, e.g. "singapore" or "24" (months); "" = any value
    company: str = ""
    date: str = ""
    note: str = ""

    def text(self) -> str:
        return f"{self.rule_id} {self.counterparty} {self.value} {self.approved_by} {self.note}"


@dataclass
class PrecedentMemory:
    items: list[Precedent] = field(default_factory=list)
    path: str | None = None

    def add(self, p: Precedent) -> None:
        self.items.append(p)
        if self.path:
            self.save(self.path)

    def find(self, rule_id: str, counterparty: str, company: str = "", value: str | None = None) -> Precedent | None:
        cp = counterparty.lower()
        cands = [p for p in self.items if p.rule_id == rule_id and p.counterparty.lower() == cp
                 and (not company or not p.company or p.company == company)]
        if value is not None:
            v = str(value).lower()
            cands = [p for p in cands if not p.value or p.value.lower() == v]
        return cands[0] if cands else None

    def search(self, query: str, k: int = 3) -> list[Precedent]:
        if not self.items:
            return []
        idx = HybridIndex([Passage(str(i), p.text()) for i, p in enumerate(self.items)])
        return [self.items[int(h.passage.id)] for h in idx.search(query, k=k)]

    def as_dicts(self) -> list[dict]:
        """The shape tools/legal_tools.py precedent_search expects."""
        return [{**asdict(p)} for p in self.items]

    def save(self, path: str | Path) -> None:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text(json.dumps([asdict(p) for p in self.items], indent=1))

    @classmethod
    def load(cls, path: str | Path) -> "PrecedentMemory":
        p = Path(path)
        items = [Precedent(**d) for d in json.loads(p.read_text())] if p.exists() else []
        return cls(items, str(p))


def scripted_precedents(packs: list[PolicyPack], n: int = 30, seed: int = 0) -> list[Precedent]:
    """`n` approvals spread over the packs' rules that have an approval route, each for one
    counterparty type, as a senior lawyer would have granted them in past deals."""
    rng = random.Random(f"precedents-{seed}")
    slots = [(p, r) for p in packs for r in p.rules if r.approval]
    if not slots:
        return []
    out, seen = [], set()
    types = [t.value for t in CounterpartyType]
    for _ in range(n * 5):
        if len(out) >= n:
            break
        pack, rule = rng.choice(slots)
        ctype = rng.choice(types)
        if (pack.company, rule.id, ctype) in seen:
            continue
        seen.add((pack.company, rule.id, ctype))
        out.append(Precedent(rule.id, ctype, rule.approval or "", company=pack.company,
                             date=f"2026-0{rng.randint(1, 9)}-{rng.randint(10, 28)}",
                             note=f"Deviation from '{rule.title}' accepted for {ctype} deals."))
    return out
