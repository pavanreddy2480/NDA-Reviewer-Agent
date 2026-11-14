"""Shared pieces of the RQ1 baselines (proposal §7: B1, B2, B2+checklist, B3).

Baselines that read policy *prose* (B1 long context, B2 naive RAG) cannot cite a rule id: the
prose has none. They cite the policy document and quote the passage, and `QuoteMapper` maps the
quote to the rule of the pack the system was given whose source quote it overlaps most, the same
quote-overlap matching that maps compiled cards to gold rules (benchmark/align.py). An unmapped
quote keeps a "PROSE-" id and counts as a false alarm, which is fair: a lawyer could not act on a
flag that points at no requirement.
"""

from __future__ import annotations

import re
from pathlib import Path

from ..data.draft import Draft
from ..policy.schema import DealContext, LawPack, PolicyPack
from ..review.findings import Finding, FindingType
from ..benchmark.align import overlap

FINDING_ITEM = {
    "type": "object",
    "properties": {
        "rule_id": {"type": "string"},
        "document": {"type": "string"},
        "quote": {"type": "string"},
        "type": {"type": "string", "enum": ["violation", "omission", "approval_needed", "statutory_risk"]},
        "evidence": {"type": "array", "items": {"type": "integer"}},
        "explanation": {"type": "string"},
    },
    "required": ["type", "evidence", "explanation"],
}
FINDINGS_SCHEMA = {"type": "object", "properties": {"findings": {"type": "array", "items": FINDING_ITEM}},
                   "required": ["findings"]}


def load_policy_docs(policy_dir: str | Path | None) -> list[tuple[str, str]]:
    """(title, text) per policy document, sorted by file name."""
    if not policy_dir or not Path(policy_dir).is_dir():
        return []
    out = []
    for p in sorted(Path(policy_dir).glob("*.md")):
        text = p.read_text(encoding="utf-8")
        m = re.search(r"^#\s+(.+)$", text, re.M)
        out.append((m.group(1).strip() if m else p.stem.replace("_", " ").title(), text))
    return out


def policy_dir_for(pack_path: str | Path) -> Path | None:
    """packs/policynda/<company>/policies next to a gold_rules.yaml or compiled cards file."""
    p = Path(pack_path).resolve()
    for d in (p.parent / "policies", p.parent.parent / "policies"):
        if d.is_dir():
            return d
    return None


def rules_text(pack: PolicyPack) -> str:
    return "\n".join(r.as_text() for r in pack.rules)


def law_text(law_pack: LawPack | None) -> str:
    if law_pack is None:
        return "(none)"
    return "\n".join(f"[{p.id}] {p.act} {p.section}: {p.title}. {p.summary} Risky pattern: {p.risk_pattern}. "
                     f"Applies under: {', '.join(p.requires_law) or 'any law'}" for p in law_pack.provisions)


def form_text(deal: DealContext) -> str:
    d = deal.model_dump(mode="json")
    return "\n".join(f"- {k}: {'(blank: read it from the NDA)' if v is None else v}" for k, v in d.items())


class QuoteMapper:
    def __init__(self, pack: PolicyPack, law_pack: LawPack | None = None, min_overlap: float = 0.5):
        self.pack, self.min = pack, min_overlap
        self.ids = {r.id for r in pack.rules} | ({p.id for p in law_pack.provisions} if law_pack else set())

    def rule_for(self, document: str, quote: str) -> str | None:
        best, best_s = None, 0.0
        for r in self.pack.rules:
            if not r.source or not r.source.quote:
                continue
            if document and r.source.document and r.source.document.lower() not in document.lower() \
                    and document.lower() not in r.source.document.lower():
                continue
            s = overlap(quote, r.source.quote)
            if s > best_s:
                best, best_s = r.id, s
        if best_s >= self.min:
            return best
        # fall back to the rule statement itself (paraphrased quotes)
        best, best_s = None, 0.0
        for r in self.pack.rules:
            s = overlap(quote, f"{r.requirement} {r.check_term}")
            if s > best_s:
                best, best_s = r.id, s
        return best if best_s >= self.min else None

    def to_findings(self, items: list, draft: Draft, reviewer: str, direction: str) -> list[Finding]:
        out = []
        for it in items if isinstance(items, list) else []:
            if not isinstance(it, dict):
                continue
            rid = str(it.get("rule_id") or "").strip()
            if rid not in self.ids:
                rid = self.rule_for(str(it.get("document", "")), str(it.get("quote", ""))) if it.get("quote") else None
                rid = rid or f"PROSE-{abs(hash(str(it.get('quote', ''))[:80])) % 10**6}"
            try:
                ftype = FindingType(it.get("type", "violation"))
            except ValueError:
                ftype = FindingType.VIOLATION
            if rid.startswith("LAW-"):
                ftype = FindingType.STATUTORY_RISK
            ev = sorted({int(i) for i in it.get("evidence", []) if isinstance(i, (int, float))
                         and 0 <= int(i) < len(draft.segments)})
            if ftype == FindingType.OMISSION:
                ev = []
            out.append(Finding(draft_id=draft.id, rule_id=rid, type=ftype, evidence=ev,
                               explanation=str(it.get("explanation", ""))[:400], confidence=0.6,
                               reviewer=reviewer, direction=direction))
        return out
