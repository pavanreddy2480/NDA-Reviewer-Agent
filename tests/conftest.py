"""Shared fixtures for the CounselCopilot test suite.

Nothing here touches the network, ContractNLI or a real model. Every test builds its own tiny
NDA, policy pack and law pack, and talks to a scripted fake LLM (`KeywordLLM`) that answers
the reviewer's prompts by looking for keywords in the segments it is shown. That keeps each
test's expected outcome readable from the fixture itself.

The suite is organised by the proposal (docs/proposal/proposal.pdf):
    §4  rule base, two-way retrieval, deal filter, hybrid RAG   test_policy_rules, test_retrieval,
                                                                 test_policy_reviewer, test_deal_facts,
                                                                 test_fields, test_checker
    §4  red-team and repair scoring (RQ2)                       test_draft, test_evaluator
    §5  tool calling, gated actions                             test_tools
    §6  PolicyNDA: ground truth, planting, labels, packs         test_gold, test_planter, test_labels,
                                                                 test_packgen, test_shipped_assets,
                                                                 test_contractnli
    §7  evaluation: metrics, CIs, TOST, kappa                   test_metrics, test_rq1
    §7/§10 backbones, cache, batch, cost                         test_llm, test_batch
"""

from __future__ import annotations

import json
import re

import pytest

from counselcopilot.data.contractnli import Annotation, NDADocument, NLILabel
from counselcopilot.llm import FakeClient, LLMRequest
from counselcopilot.policy.schema import DealContext, LawPack, PolicyPack
from counselcopilot.review.checker import CHECK_SYSTEM
from counselcopilot.review.fields import FIELD_QUESTIONS

ALL_HYPOTHESES = ["nda-1", "nda-2", "nda-3", "nda-4", "nda-5", "nda-7", "nda-8", "nda-10", "nda-11",
                  "nda-12", "nda-13", "nda-15", "nda-16", "nda-17", "nda-18", "nda-19", "nda-20"]

# ------------------------------------------------------------------ terms the fake model recognises

RETURN_TERM = "The Receiving Party must return or destroy Confidential Information when the agreement ends."
ORAL_TERM = "Confidential Information includes information disclosed orally."
NONSOLICIT_TERM = "A party shall not solicit or hire the other party's employees."
NONCOMPETE_TERM = "A party is restricted from competing with the other party."
DTSA_TERM = "The agreement gives notice of whistleblower immunity for disclosing a trade secret."

# term -> (keyword that makes the fake model answer Entailment, keyword for Contradiction)
KEYWORDS = {
    RETURN_TERM: ("destroy", "may keep all copies"),
    ORAL_TERM: ("orally", "oral disclosures are not"),
    NONSOLICIT_TERM: ("solicit", None),
    NONCOMPETE_TERM: ("compete", None),
    DTSA_TERM: ("whistleblower", None),
}


# ------------------------------------------------------------------ fake LLM

def _segments(prompt: str) -> dict[int, str]:
    return {int(m.group(1)): m.group(2) for m in re.finditer(r"^\[(\d+)\] (.*)$", prompt, re.M)}


class KeywordLLM(FakeClient):
    """Answers the reviewer's three kinds of prompt from fixed facts.

    - rule checks (CHECK_SYSTEM): Entailment if a shown segment has the term's keyword,
      Contradiction if one has its contradiction keyword, else NotMentioned;
    - field questions: the value in `fields`, citing the shown segments that contain `field_hints`;
    - the personal-data question: `personal_data`.
    `broken` makes every reply unparseable, `confidence` sets the reported confidence.
    """

    def __init__(self, fields: dict | None = None, field_hints: dict | None = None,
                 personal_data: bool = False, keywords: dict | None = None, broken: bool = False,
                 confidence: float = 0.9, name: str = "keyword-fake"):
        super().__init__(self._respond, model=name, name=name)
        self.fields = fields or {}
        self.field_hints = field_hints or {}
        self.personal_data = personal_data
        self.keywords = {**KEYWORDS, **(keywords or {})}
        self.broken = broken
        self.confidence = confidence

    def _respond(self, req: LLMRequest) -> str:
        if self.broken:
            return "I am not going to answer in JSON."
        sys_text = req.messages[0].content
        prompt = req.messages[-1].content
        segs = _segments(prompt)
        if sys_text == CHECK_SYSTEM or prompt.startswith("CONTRACT TERM:"):
            term = re.search(r"(?:STATEMENT|CONTRACT TERM): (.*)", prompt).group(1).strip()
            yes, no = self.keywords.get(term, (None, None))
            con = [i for i, s in segs.items() if no and no in s.lower()]
            ent = [i for i, s in segs.items() if yes and yes in s.lower()]
            if con:
                label, ev = "Contradiction", con
            elif ent:
                label, ev = "Entailment", ent
            else:
                label, ev = "NotMentioned", []
            return json.dumps({"rationale": "scripted", "label": label, "evidence": ev,
                               "confidence": self.confidence})
        if prompt.startswith("QUESTION:"):
            field = next(f for f, q in FIELD_QUESTIONS.items() if q in prompt)
            hint = self.field_hints.get(field)
            ev = [i for i, s in segs.items() if hint and hint in s.lower()]
            return json.dumps({"value": self.fields.get(field), "evidence": ev})
        if "personal data" in sys_text:
            return json.dumps({"rationale": "scripted", "personal_data": self.personal_data, "evidence": []})
        return json.dumps({})

    # helpers for assertions
    def prompts_with(self, text: str) -> list[LLMRequest]:
        return [r for r in self.requests if text in r.messages[-1].content]

    def check_requests(self) -> list[LLMRequest]:
        return [r for r in self.requests if r.messages[0].content == CHECK_SYSTEM]


@pytest.fixture
def keyword_llm():
    return KeywordLLM


# ------------------------------------------------------------------ packs

def make_pack(company: str = "TestCo", rules: list[dict] | None = None) -> PolicyPack:
    """A small pack in the PolicyNDA format: anchored require/forbid rules, field rules with a
    min/max pair, an approval route and a cross-reference."""
    rules = rules if rules is not None else [
        {"id": "P-01", "title": "Return or destruction", "kind": "require", "term": RETURN_TERM,
         "requirement": "Vendor and partner NDAs must require return or destruction of our information.",
         "applies_if": "counterparty in ['vendor', 'partner']", "anchor": {"hypothesis": "nda-16"},
         "severity": "high", "keywords": ["return", "destroy"],
         "source": {"document": "Vendor Policy", "section": "4.2", "quote": "Vendors must give it back."}},
        {"id": "P-02", "title": "Oral disclosures covered", "kind": "require", "term": ORAL_TERM,
         "requirement": "Oral disclosures must be covered.", "anchor": {"hypothesis": "nda-3"},
         "keywords": ["oral", "orally"]},
        {"id": "P-03", "title": "No non-solicitation for customers", "kind": "forbid", "term": NONSOLICIT_TERM,
         "requirement": "Customer NDAs must not contain a non-solicitation clause.",
         "applies_if": "counterparty == 'customer'", "anchor": {"hypothesis": "nda-18"},
         "keywords": ["solicit", "hire"]},
        {"id": "P-04", "title": "Minimum term with personal data", "kind": "field",
         "requirement": "With personal data, confidentiality lasts at least 36 months.",
         "applies_if": "personal_data", "constraint": {"field": "confidentiality_term_months", "op": ">=", "value": 36},
         "refs": ["P-06"]},
        {"id": "P-05", "title": "Governing law", "kind": "field",
         "requirement": "Delaware or New York law unless the General Counsel approves.",
         "constraint": {"field": "governing_law", "op": "in", "value": ["delaware", "new york"]},
         "approval": "General Counsel"},
        {"id": "P-06", "title": "Maximum term", "kind": "field",
         "requirement": "Confidentiality lasts at most 60 months.",
         "constraint": {"field": "confidentiality_term_months", "op": "<=", "value": 60}},
    ]
    return PolicyPack.model_validate({"company": company, "rules": rules})


@pytest.fixture
def pack() -> PolicyPack:
    return make_pack()


def make_law_pack(checked: bool = False) -> LawPack:
    who = ["teammate-a", "teammate-b"] if checked else []
    return LawPack.model_validate({"version": "test", "as_of": "2026-10-25", "provisions": [
        {"id": "LAW-CA-BPC-16600", "act": "California Business and Professions Code", "section": "§16600",
         "title": "Non-competes void", "summary": "Contracts restraining a lawful business are void.",
         "risk_pattern": NONCOMPETE_TERM, "requires_law": ["california"], "checked_by": who},
        {"id": "LAW-DTSA-1833B", "act": "Defend Trade Secrets Act", "section": "§1833(b)(3)",
         "title": "Whistleblower notice", "summary": "Employers must give notice of immunity.",
         "risk_pattern": DTSA_TERM, "kind": "require", "applies_if": "counterparty == 'employee'",
         "severity": "medium", "checked_by": who},
        {"id": "LAW-PENALTY", "act": "Common law", "section": "§356", "title": "Penalty clauses",
         "summary": "Unreasonable fixed sums are penalties.", "risk_pattern": "A fixed penalty is payable.",
         "requires_law": ["us"], "risk_level": "possible_risk", "checked_by": who},
    ]})


@pytest.fixture
def law_pack() -> LawPack:
    return make_law_pack()


def deal(**kw) -> DealContext:
    base = {"company": "TestCo", "counterparty_type": "vendor", "personal_data": False, "governing_law": "delaware"}
    return DealContext(**{**base, **kw})


@pytest.fixture
def make_deal():
    return deal


# ------------------------------------------------------------------ NDAs

COMPLIANT_SEGMENTS = [
    "MUTUAL NON-DISCLOSURE AGREEMENT",
    "Confidential Information includes information disclosed orally or in writing.",
    "On request the Receiving Party shall return or destroy all Confidential Information.",
    "The obligations of confidentiality last for four (4) years.",
    "This Agreement is governed by the laws of the State of Delaware.",
    "Each party shall bear its own costs.",
]


def make_doc(segments: list[str] | None = None, doc_id: int = 1,
             labels: dict[str, tuple[str, tuple[int, ...]]] | None = None, split: str = "test") -> NDADocument:
    """An NDADocument whose spans are the given segments. Every hypothesis gets a label:
    NotMentioned unless `labels` says otherwise."""
    segments = segments if segments is not None else COMPLIANT_SEGMENTS
    text, spans, pos = "", [], 0
    for s in segments:
        spans.append((pos, pos + len(s)))
        text += s + "\n"
        pos += len(s) + 1
    labels = labels or {}
    anns = {h: Annotation(NLILabel(labels.get(h, ("NotMentioned", ()))[0]), tuple(labels.get(h, ("", ()))[1]))
            for h in ALL_HYPOTHESES}
    return NDADocument(doc_id, f"nda_{doc_id}.txt", text, spans, anns, "search-pdf", "", split)


@pytest.fixture
def doc_factory():
    return make_doc
