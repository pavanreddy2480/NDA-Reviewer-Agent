"""Consistency reviewer (design §3.1): internal conflicts found with deterministic tools.

No model is needed for these checks, so they are exact and free:
- `term_usages`: where a defined term is defined and used; a term defined twice with different
  wording is definition drift;
- `resolve_cross_ref`: "Section 7.2" must point at a section the NDA has;
- `normalise_dates` / conflicting durations: two different lengths for the same obligation
  (confidentiality "three (3) years" in one clause and "five (5) years" in another).

The same functions are tools the agents can call (`consistency_tools`). Findings use rule ids
starting "CONS-"; PolicyNDA has no gold for them, so RQ1 scoring reports them separately and
never counts them as false alarms.
"""

from __future__ import annotations

import re
from collections import defaultdict

from ..data.draft import Draft
from .findings import Finding, FindingType
from .fields import _duration
from .frames import clause_type

_DEF = re.compile(r"[\"“]([A-Z][A-Za-z ]{1,40}?)[\"”]\s*(?:\)|shall mean|means|has the meaning|refers to)", re.S)
_DEF_AFTER = re.compile(r"\((?:the\s+|each\s+a\s+|collectively,?\s+)?[\"“]([A-Z][A-Za-z ]{1,40}?)[\"”]\)")
_REF = re.compile(r"\b(?:Section|Clause|Paragraph|Article)s?\s+(\d+(?:\.\d+)*)(?:\s*\(([a-z])\))?", re.I)
_HEAD = re.compile(r"^\s*(?:Section|Clause|Article)?\s*(\d+(?:\.\d+)*)[.)]?\s+\S")
_DUR = re.compile(r"(?:[a-z]+(?:-[a-z]+)?\s*)?\(?\d+\)?\s*(?:years?|months?)|\b(?:one|two|three|four|five|six|seven|"
                  r"eight|nine|ten)\s+(?:years?|months?)", re.I)

CONS_DEF, CONS_XREF, CONS_TERM = "CONS-DEF", "CONS-XREF", "CONS-TERM"


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s.strip().lower())


def term_usages(draft: Draft, term: str) -> dict:
    """Segments that define `term` and segments that use it."""
    defs, uses = [], []
    for i, s in enumerate(draft.segments):
        if any(m.group(1).strip() == term for m in list(_DEF.finditer(s)) + list(_DEF_AFTER.finditer(s))):
            defs.append(i)
        elif re.search(rf"\b{re.escape(term)}\b", s):
            uses.append(i)
    return {"term": term, "defined_in": defs, "used_in": uses}


def defined_terms(draft: Draft) -> dict[str, list[int]]:
    out: dict[str, list[int]] = defaultdict(list)
    for i, s in enumerate(draft.segments):
        for m in list(_DEF.finditer(s)) + list(_DEF_AFTER.finditer(s)):
            out[m.group(1).strip()].append(i)
    return dict(out)


def section_numbers(draft: Draft) -> set[str]:
    out = set()
    for s in draft.segments:
        m = _HEAD.match(s)
        if m:
            num = m.group(1)
            out.add(num)
            parts = num.split(".")
            for k in range(1, len(parts)):
                out.add(".".join(parts[:k]))
    return out


def resolve_cross_ref(draft: Draft, ref: str) -> dict:
    """Does "Section <ref>" exist in this NDA? Unknown when the NDA has no numbered headings."""
    nums = section_numbers(draft)
    if not nums:
        return {"ref": ref, "status": "unknown", "reason": "the NDA has no numbered sections"}
    return {"ref": ref, "status": "ok" if ref in nums else "missing", "sections": sorted(nums)[:50]}


def normalise_dates(text: str) -> dict:
    """Every duration in `text`, in months."""
    return {"durations_months": [d for d in (_duration(m.group(0), "months") for m in _DUR.finditer(text)) if d]}


def _defs_conflict(draft: Draft, segs: list[int], term: str) -> bool:
    texts = {_norm(draft.segments[i]) for i in segs}
    return len(texts) > 1


def check_consistency(draft: Draft) -> list[Finding]:
    findings: list[Finding] = []
    # 1. definition drift: one term, two different defining clauses
    for term, segs in defined_terms(draft).items():
        if len(segs) > 1 and _defs_conflict(draft, segs, term):
            findings.append(Finding(draft_id=draft.id, rule_id=f"{CONS_DEF}-{re.sub(r'[^A-Za-z]', '', term)[:20]}",
                                    type=FindingType.INCONSISTENCY, evidence=segs, confidence=0.7,
                                    reviewer="consistency_reviewer", direction="tool", severity="medium",
                                    explanation=f'"{term}" is defined {len(segs)} times with different wording.'))
    # 2. broken cross-references
    nums = section_numbers(draft)
    if nums:
        for i, s in enumerate(draft.segments):
            if _HEAD.match(s) and _REF.search(s[:12]):
                continue  # the heading itself
            for m in _REF.finditer(s):
                if m.group(1) not in nums:
                    findings.append(Finding(draft_id=draft.id, rule_id=f"{CONS_XREF}-{m.group(1)}",
                                            type=FindingType.INCONSISTENCY, evidence=[i], confidence=0.8,
                                            reviewer="consistency_reviewer", direction="tool", severity="low",
                                            explanation=f"Refers to Section {m.group(1)}, which this NDA does not have."))
    # 3. conflicting durations for the confidentiality term
    terms: dict[float, list[int]] = defaultdict(list)
    for i, s in enumerate(draft.segments):
        if clause_type(s) == "confidentiality_term" and "confidential" in s.lower():
            for d in normalise_dates(s)["durations_months"]:
                if d < 9999:
                    terms[d].append(i)
                    break
    if len(terms) > 1:
        ev = sorted({i for v in terms.values() for i in v})
        findings.append(Finding(draft_id=draft.id, rule_id=CONS_TERM, type=FindingType.INCONSISTENCY, evidence=ev,
                                confidence=0.6, reviewer="consistency_reviewer", direction="tool", severity="medium",
                                explanation="The confidentiality term is stated as "
                                            + ", ".join(f"{int(k)} months" for k in sorted(terms)) + "."))
    # one finding per id
    seen, out = set(), []
    for f in findings:
        if f.rule_id not in seen:
            seen.add(f.rule_id)
            out.append(f)
    return out


def is_consistency(rule_id: str) -> bool:
    return rule_id.startswith("CONS-")


def consistency_tools(draft: Draft):
    """The functions above as tools for the JSON agent (tools/registry.py)."""
    from ..tools.registry import Tool

    s = lambda **p: {"type": "object", "properties": p, "required": list(p), "additionalProperties": False}
    return [
        Tool("term_usages", "Where a defined term is defined and used in the NDA.", s(term={"type": "string"}),
             lambda term: term_usages(draft, term)),
        Tool("resolve_cross_ref", "Check that a section number referred to exists in the NDA.",
             s(ref={"type": "string"}), lambda ref: resolve_cross_ref(draft, ref)),
        Tool("normalise_dates", "Durations in a piece of text, in months.", s(text={"type": "string"}),
             normalise_dates),
    ]
