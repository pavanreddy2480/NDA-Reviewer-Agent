"""Planner agent (design §3.1): picks which reviewers run, from the deal and the clause types present.

The policy reviewer always runs: it is the only path to omissions, and skipping it can never be
cheaper than a missed rule. The planner decides whether the law and risk reviewer and the
consistency reviewer are worth running for this NDA (a Delaware vendor NDA with no restrictive
covenants needs less law review than a California employee NDA with a non-compete).

Modes:
- "model": the backbone reads the deal form and the clause-type profile and answers in JSON;
  an unreadable reply falls back to running everything;
- "rules": the same decision from fixed rules (no model call);
- "fixed": every reviewer, every time (the "planner -> fixed pipeline" ablation).
The plan, its rationale and the clause profile are logged so the planner's choices can be
analysed step by step.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

from ..data.draft import Draft
from ..llm import LLMClient, PendingBatch, system, user
from ..policy.schema import DealContext
from ..review.frames import clause_type

REVIEWERS = ("policy", "law", "consistency")
DESCRIPTIONS = {
    "policy": "checks every company rule that applies to this deal (violations and omissions); always runs",
    "law": "checks US law provisions (DTSA notice, SEC 21F-17, Speak Out Act, California §16600, penalties, "
           "CCPA) and dispute-risk patterns",
    "consistency": "deterministic checks for definition drift, broken cross-references and conflicting durations",
}

PLAN_SCHEMA = {
    "type": "object",
    "properties": {"reviewers": {"type": "array", "items": {"type": "string", "enum": list(REVIEWERS)}},
                   "rationale": {"type": "string"}},
    "required": ["reviewers", "rationale"],
}

PLAN_SYSTEM = """You plan the review of an NDA draft. Choose which reviewers to run:
""" + "\n".join(f"- {k}: {v}" for k, v in DESCRIPTIONS.items()) + """
Run "law" whenever the counterparty is an employee, the governing law is a US state or unknown, or the NDA has restrictive covenants (non-compete, non-solicit), penalties or reporting restrictions. Run "consistency" when the NDA has numbered sections, several definitions or several durations. When unsure, include the reviewer.
Reply with JSON {"reviewers": [...], "rationale": one sentence}."""

RISK_TYPES = {"non_compete", "non_solicit", "remedies"}


@dataclass
class Plan:
    reviewers: list[str]
    rationale: str = ""
    profile: dict[str, int] = field(default_factory=dict)
    mode: str = "fixed"


def clause_profile(draft: Draft) -> dict[str, int]:
    return dict(Counter(clause_type(s) for s in draft.segments))


class Planner:
    def __init__(self, llm: LLMClient | None = None, mode: str = "model"):
        if mode not in ("model", "rules", "fixed"):
            raise ValueError(f"unknown planner mode {mode!r}")
        self.llm, self.mode = llm, mode

    def _rules(self, draft: Draft, deal: DealContext, profile: dict[str, int], law_available: bool) -> Plan:
        chosen = ["policy"]
        why = []
        law = (deal.counterparty_type.value == "employee" or deal.governing_law in (None, "unknown")
               or deal.variables().get("us_law") or any(profile.get(t) for t in RISK_TYPES))
        if law_available and law:
            chosen.append("law")
            why.append("US law or restrictive covenants in play")
        if profile.get("definition", 0) >= 2 or len(draft.segments) >= 25:
            chosen.append("consistency")
            why.append("several definitions or a long NDA")
        return Plan(chosen, "; ".join(why) or "policy rules only", profile, "rules")

    def plan(self, draft: Draft, deal: DealContext, law_available: bool = True) -> Plan:
        profile = clause_profile(draft)
        available = [r for r in REVIEWERS if law_available or r != "law"]
        if self.mode == "fixed":
            return Plan(available, "fixed pipeline", profile, "fixed")
        if self.mode == "rules" or self.llm is None:
            return self._rules(draft, deal, profile, law_available)
        form = deal.model_dump(mode="json")
        try:
            out = self.llm.complete_json(
                [system(PLAN_SYSTEM),
                 user(f"DEAL FORM: {form}\nCLAUSE TYPES PRESENT: {profile}\nNUMBER OF SEGMENTS: {len(draft.segments)}\n"
                      f"AVAILABLE REVIEWERS: {available}")],
                PLAN_SCHEMA, max_tokens=150, tag="planner")
            picked = [r for r in out.get("reviewers", []) if r in available]
            rationale = str(out.get("rationale", ""))
        except PendingBatch:
            raise
        except Exception:
            picked, rationale = list(available), "planner reply unreadable: run everything"
        if not picked and not rationale:
            picked, rationale = list(available), "empty plan: run everything"
        if "policy" not in picked:  # the only route to omissions is never skipped
            picked.insert(0, "policy")
        return Plan([r for r in REVIEWERS if r in picked], rationale, profile, "model")
