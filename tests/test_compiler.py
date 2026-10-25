"""Proposal §4: the policy compiler turns prose policies into a rule base (requirement cards, design
§20), the model judges when each card applies, and compiled cards are scored against the gold
rule list they never saw (design D17)."""

import json

import pytest

from conftest import COMPLIANT_SEGMENTS, ORAL_TERM, RETURN_TERM, KeywordLLM
from counselcopilot.benchmark.align import align, overlap, remap_findings
from counselcopilot.data.draft import Draft
from counselcopilot.llm import FakeClient
from counselcopilot.policy.compiler import COMPILER_SYSTEM, PolicyCompiler, quote_found, save_compiled
from counselcopilot.policy.schema import DealContext, PolicyPack
from counselcopilot.review.applicability import APPLY_SYSTEM, judge_applicability
from counselcopilot.review.findings import Finding, FindingType
from counselcopilot.review.policy_reviewer import PolicyReviewer, ReviewConfig
from counselcopilot.retrieval.index import HybridIndex, Passage

POLICY = """# Vendor Policy

## 4. Information handling

4.2 Every vendor agreement must require the vendor to return or destroy our information when the work ends, where the vendor handles personal data.

4.3 Information we share in meetings or calls must be protected even when it is only spoken.

4.4 Confidentiality obligations must last at least three years.
"""

CARDS = [
    {"title": "Return or destruction", "kind": "require", "statement": RETURN_TERM,
     "applies_when": "vendor deals where personal data is shared", "applies_if": "counterparty == 'vendor' and personal_data",
     "severity": "high", "section": "4.2", "keywords": ["return", "destroy"],
     "quote": "Every vendor agreement must require the vendor to return or destroy our information when the work ends"},
    {"title": "Oral disclosures", "kind": "require", "statement": ORAL_TERM, "applies_when": "always",
     "applies_if": "True", "severity": "medium", "section": "4.3",
     "quote": "Information we share in meetings or calls must be protected even when it is only spoken."},
    {"title": "Minimum term", "kind": "field", "statement": "Confidentiality lasts at least 36 months.",
     "applies_when": "always", "applies_if": "len(x)", "field": "confidentiality_term_months", "op": ">=",
     "value": 36, "severity": "medium", "section": "4.4",
     "quote": "Confidentiality obligations must last at least three years."},
    {"title": "Invented", "kind": "forbid", "statement": "No arbitration.", "applies_when": "always",
     "applies_if": "True", "severity": "low", "section": "9", "quote": "Arbitration is never allowed in any agreement."},
]


def compiler_llm(cards=CARDS):
    return FakeClient(lambda req: json.dumps({"cards": cards}) if req.messages[0].content == COMPILER_SYSTEM else "{}")


@pytest.fixture
def policy_dir(tmp_path):
    d = tmp_path / "policies"
    d.mkdir()
    (d / "vendor_policy.md").write_text(POLICY)
    return d


def compiled(policy_dir):
    return PolicyCompiler(compiler_llm()).compile("TestCo", policy_dir)


# ------------------------------------------------------------------ compiler

def test_cards_keep_their_source_and_get_card_ids(policy_dir):
    pack, report = compiled(policy_dir)
    assert [r.id for r in pack.rules] == ["C-01", "C-02", "C-03"]
    first = pack.rules[0]
    assert first.source.document == "Vendor Policy" and first.source.section == "4.2"
    assert first.term == RETURN_TERM and first.applies_when == "vendor deals where personal data is shared"
    assert report.documents == 1 and report.cards == 3


def test_card_whose_quote_is_not_in_the_policy_is_dropped(policy_dir):
    pack, report = compiled(policy_dir)
    assert report.dropped_quote == ["Invented"]
    assert "No arbitration." not in {r.term for r in pack.rules}


def test_always_means_no_condition_and_a_bad_expression_falls_back_to_true(policy_dir):
    pack, report = compiled(policy_dir)
    oral, term = pack.rule("C-02"), pack.rule("C-03")
    assert oral.applies_when == "" and oral.applies_if == "True"
    assert term.applies_if == "True" and report.unstructured == ["Minimum term"]  # "len(x)" is not allowed
    assert pack.rule("C-01").applies_if == "counterparty == 'vendor' and personal_data"


def test_field_cards_become_field_rules(policy_dir):
    c = compiled(policy_dir)[0].rule("C-03").constraint
    assert (c.field, c.op, c.value) == ("confidentiality_term_months", ">=", 36)


def test_malformed_card_is_dropped_not_fatal(policy_dir):
    bad = [{**CARDS[2], "field": "colour_of_paper"}]
    pack, report = PolicyCompiler(compiler_llm(bad)).compile("TestCo", policy_dir)
    assert pack.rules == [] and report.dropped_invalid == ["Minimum term"]


def test_quote_matching_ignores_whitespace_and_markdown():
    assert quote_found("must  last at\nleast three **years**", "It must last at least three years.")
    assert not quote_found("short", "short")  # too short to be evidence


def test_compiled_pack_round_trips(tmp_path, policy_dir):
    pack, report = compiled(policy_dir)
    save_compiled(pack, report, tmp_path / "c.yaml", "fake")
    assert PolicyPack.load(tmp_path / "c.yaml").rule("C-01").applies_when == pack.rule("C-01").applies_when


# ------------------------------------------------------------------ model-judged applicability

def applies_llm(answers):
    def respond(req):
        if req.messages[0].content == APPLY_SYSTEM:
            return json.dumps({"answers": [{"id": k, "applies": v, "rationale": "r"} for k, v in answers.items()]})
        return KeywordLLM(fields={"confidentiality_term_months": 48})._respond(req)
    return FakeClient(respond)


def index(draft):
    return HybridIndex([Passage(str(i), s) for i, s in enumerate(draft.segments)])


def test_model_answers_yes_no_unknown(policy_dir):
    pack, _ = compiled(policy_dir)
    draft = Draft("d", list(COMPLIANT_SEGMENTS))
    d = DealContext(company="TestCo", counterparty_type="vendor", personal_data=None)
    out, why = judge_applicability(applies_llm({"C-01": "unknown"}), pack.rules, d, draft, index(draft))
    assert out == {"C-01": None} and why["C-01"] == "r"  # only cards with a condition are asked


def test_the_reviewer_uses_the_model_for_cards_and_checks_unknown_ones(policy_dir):
    pack, _ = compiled(policy_dir)
    draft = Draft("d", list(COMPLIANT_SEGMENTS))
    d = DealContext(company="TestCo", counterparty_type="customer", personal_data=False, governing_law="delaware")
    cfg = ReviewConfig(max_workers=1)
    no = PolicyReviewer(applies_llm({"C-01": "no"}), pack, cfg).review(draft, d)
    unknown = PolicyReviewer(applies_llm({"C-01": "unknown"}), pack, cfg).review(draft, d)
    yes = PolicyReviewer(applies_llm({"C-01": "yes"}), pack, cfg).review(draft, d)
    assert "C-01" not in no.rules_in_scope
    assert "C-01" in unknown.rules_in_scope and unknown.undecided_rules == ["C-01"]
    assert "C-01" in yes.applicable_rules  # the model overrules the structured condition (customer)


def test_structured_ablation_ignores_the_model(policy_dir):
    pack, _ = compiled(policy_dir)
    draft = Draft("d", list(COMPLIANT_SEGMENTS))
    d = DealContext(company="TestCo", counterparty_type="customer", personal_data=False, governing_law="delaware")
    llm = applies_llm({"C-01": "yes"})
    res = PolicyReviewer(llm, pack, ReviewConfig(max_workers=1, applicability="structured")).review(draft, d)
    assert "C-01" not in res.rules_in_scope
    assert not [r for r in llm.requests if r.messages[0].content == APPLY_SYSTEM]


# ------------------------------------------------------------------ scoring compiled cards against gold

GOLD = PolicyPack.model_validate({"company": "TestCo", "rules": [
    {"id": "P-01", "title": "Return", "kind": "require", "requirement": "x", "term": RETURN_TERM,
     "source": {"document": "Vendor Policy", "section": "4.2",
                "quote": "Every vendor agreement must require the vendor to return or destroy our information "
                         "when the work ends, where the vendor handles personal data."}},
    {"id": "P-02", "title": "Term", "kind": "field", "requirement": "x",
     "constraint": {"field": "confidentiality_term_months", "op": ">=", "value": 36},
     "source": {"document": "Vendor Policy", "quote": "Confidentiality obligations must last at least three years."}},
    {"id": "P-03", "title": "Missed", "kind": "require", "requirement": "x",
     "source": {"document": "Vendor Policy", "quote": "Something the compiler never found in the policy text."}},
]})


def test_cards_match_gold_rules_by_quote(policy_dir):
    pack, _ = compiled(policy_dir)
    a = align(pack, GOLD)
    assert a.card_to_gold == {"C-01": "P-01", "C-02": None, "C-03": "P-02"}
    rep = a.report(GOLD)
    assert rep["recall"] == round(2 / 3, 3) and rep["precision"] == round(2 / 3, 3)
    assert rep["missed_gold"] == ["P-03"] and rep["unmatched_cards"] == ["C-02"]


def test_field_cards_only_match_field_rules_on_the_same_field(policy_dir):
    pack, _ = compiled(policy_dir)
    other = GOLD.model_copy(deep=True)
    other.rules[1].constraint.field = "survival_months"
    assert align(pack, other).card_to_gold["C-03"] is None


def test_overlap_is_relative_to_the_shorter_quote():
    assert overlap("return or destroy", "they must return or destroy it all") == 1.0
    assert overlap("", "x") == 0.0


def test_findings_move_to_gold_ids_and_split_cards_merge():
    from counselcopilot.benchmark.align import Alignment

    a = Alignment({"C-01": "P-01", "C-04": "P-01", "C-02": None})
    f = lambda rid, c: Finding(draft_id="d", rule_id=rid, type=FindingType.OMISSION, confidence=c)
    out = remap_findings([f("C-01", 0.6), f("C-04", 0.9), f("C-02", 0.5), f("LAW-PENALTY", 0.7)], a)
    assert sorted((x.rule_id, x.confidence) for x in out) == [("C-02", 0.5), ("LAW-PENALTY", 0.7), ("P-01", 0.9)]
