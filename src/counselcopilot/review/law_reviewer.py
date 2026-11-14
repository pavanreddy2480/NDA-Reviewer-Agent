"""Law and dispute-risk reviewer (design §3.1).

Checks the NDA against the curated US law pack (DTSA notice, SEC Rule 21F-17, Speak Out Act,
Cal. B&P Code §16600, penalty clauses, CCPA) with the same check primitive and retrieval as the
policy reviewer, so a law finding cites a statute id and the NDA segments exactly like a policy
finding. Findings are worded as risk ("risk under §16600"), never as advice.

It also flags two dispute-risk patterns with deterministic tools (rule ids "RISK-..."; PolicyNDA
has no gold for them, so they are reported, not scored):
- RISK-FORUM: disputes go to courts of one place while another place's law governs;
- RISK-REMEDY: no injunctive or equitable relief for a breach of confidence.
"""

from __future__ import annotations

import re

from ..data.draft import Draft
from ..llm import LLMClient
from ..policy.schema import DealContext, LawPack, PolicyPack
from .findings import Finding, FindingType
from .frames import regex_frames
from .policy_reviewer import PolicyReviewer, ReviewConfig, ReviewResult

_REMEDY = re.compile(r"injunct\w*|equitable relief|specific performance|irreparable", re.I)


def dispute_risks(draft: Draft, governing_law: str | None) -> list[Finding]:
    out = []
    frames = regex_frames(draft)
    forum = next((f for f in frames if f.clause_type == "dispute_forum" and f.object), None)
    if forum is not None and governing_law not in (None, "unknown"):
        from ..policy.jurisdictions import is_jurisdiction, normalise_jurisdiction

        place = normalise_jurisdiction(forum.object)
        if is_jurisdiction(place) and place != governing_law:
            out.append(Finding(draft_id=draft.id, rule_id="RISK-FORUM", type=FindingType.STATUTORY_RISK,
                               evidence=[forum.segment], confidence=0.6, reviewer="law_reviewer",
                               direction="tool", severity="low",
                               explanation=f"Possible risk: disputes go to {place} while {governing_law} law governs."))
    if len(draft.segments) > 15 and not any(_REMEDY.search(s) for s in draft.segments):
        out.append(Finding(draft_id=draft.id, rule_id="RISK-REMEDY", type=FindingType.STATUTORY_RISK, evidence=[],
                           confidence=0.5, reviewer="law_reviewer", direction="tool", severity="low",
                           explanation="Possible risk: no injunctive or equitable relief for a breach of confidence."))
    return out


def is_dispute_risk(rule_id: str) -> bool:
    return rule_id.startswith("RISK-")


class LawReviewer:
    def __init__(self, llm: LLMClient, law_pack: LawPack, config: ReviewConfig | None = None,
                 checker_llm: LLMClient | None = None, encoder=None, reranker=None, dispute_patterns: bool = True):
        empty = PolicyPack(company="(law pack)", rules=[])
        self.inner = PolicyReviewer(llm, empty, config, encoder, reranker, law_pack=law_pack,
                                    checker_llm=checker_llm, name="law_reviewer")
        self.dispute_patterns = dispute_patterns

    def review(self, draft: Draft, deal: DealContext) -> ReviewResult:
        res = self.inner.review(draft, deal)
        if self.dispute_patterns:
            res.findings = res.findings + dispute_risks(draft, res.deal.governing_law if res.deal else None)
        return res
