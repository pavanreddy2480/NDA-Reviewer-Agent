"""The rule-check primitive and the findings ledger (proposal §4, Figures 1 and 2).

A require rule that is not mentioned is an omission, one that is contradicted is a violation; a
forbid rule that is entailed is a violation; a rule with an approval route becomes an
approval-gated deviation; a law-pack provision becomes a statutory risk. Gold (benchmark/gold.py)
must use the same mapping, or every system is scored against the wrong type."""

import json

import pytest

from conftest import KeywordLLM, ORAL_TERM, make_law_pack, make_pack
from counselcopilot.benchmark.gold import finding_type
from counselcopilot.data.contractnli import NLILabel
from counselcopilot.data.draft import Draft
from counselcopilot.llm import FakeClient, PendingBatch
from counselcopilot.review.checker import CheckResult, finding_from_check, run_check
from counselcopilot.review.findings import Finding, FindingType, Ledger

DRAFT = Draft("d1", ["Header.", "Confidential Information includes information disclosed orally.", "Costs."])


def fixed(reply: dict | str) -> FakeClient:
    return FakeClient(lambda req: reply if isinstance(reply, str) else json.dumps(reply))


# ------------------------------------------------------------------ run_check

def test_check_finds_the_term_and_cites_it():
    res = run_check(KeywordLLM(), ORAL_TERM, DRAFT, [0, 1, 2])
    assert res.label == "Entailment" and res.evidence == [1] and res.shown == [0, 1, 2]


def test_check_without_segments_is_not_mentioned_without_a_call():
    llm = KeywordLLM()
    res = run_check(llm, ORAL_TERM, DRAFT, [])
    assert res.label == "NotMentioned" and llm.requests == []


def test_model_only_sees_the_retrieved_segments():
    llm = KeywordLLM()
    run_check(llm, ORAL_TERM, DRAFT, [0, 2])
    prompt = llm.requests[0].messages[-1].content
    assert "[0] Header." in prompt and "[2] Costs." in prompt and "[1]" not in prompt


def test_evidence_outside_shown_segments_is_dropped():
    res = run_check(fixed({"rationale": "", "label": "Entailment", "evidence": [1, 7, "x"], "confidence": 0.8}),
                    "t", DRAFT, [0, 1])
    assert res.evidence == [1]


def test_not_mentioned_carries_no_evidence():
    res = run_check(fixed({"rationale": "", "label": "NotMentioned", "evidence": [1], "confidence": 0.8}),
                    "t", DRAFT, [0, 1])
    assert res.evidence == []


@pytest.mark.parametrize("conf, expected", [(1.7, 1.0), (-2, 0.0), ("high", 0.5), (None, 0.5)])
def test_confidence_is_clamped(conf, expected):
    res = run_check(fixed({"rationale": "", "label": "Entailment", "evidence": [], "confidence": conf}),
                    "t", DRAFT, [0])
    assert res.confidence == expected


def test_unknown_label_becomes_not_mentioned():
    res = run_check(fixed({"rationale": "", "label": "Maybe", "evidence": [], "confidence": 0.9}), "t", DRAFT, [0])
    assert res.label == "NotMentioned" and not res.error


def test_malformed_output_is_a_failed_check_not_a_crash():
    res = run_check(KeywordLLM(broken=True), ORAL_TERM, DRAFT, [0, 1])
    assert res.error and res.confidence == 0.0


def test_pending_batch_is_not_swallowed():
    class Queued(FakeClient):
        def complete(self, *a, **k):
            raise PendingBatch("queued")

    with pytest.raises(PendingBatch):
        run_check(Queued(), "t", DRAFT, [0])


# ------------------------------------------------------------------ label -> finding

def res(label: str, ev=(1,)) -> CheckResult:
    return CheckResult(label, list(ev) if label != "NotMentioned" else [], 0.9, "why")


PACK = make_pack(rules=[
    {"id": "P-01", "title": "r", "requirement": "r", "kind": "require"},
    {"id": "P-02", "title": "f", "requirement": "f", "kind": "forbid"},
    {"id": "P-03", "title": "a", "requirement": "a", "kind": "require", "approval": "General Counsel"},
    {"id": "P-04", "title": "b", "requirement": "b", "kind": "forbid", "approval": "CFO"},
])
LAW = {r.id: r for r in make_law_pack().as_rules()}


@pytest.mark.parametrize("rule_id, label, expected", [
    ("P-01", "Entailment", None),
    ("P-01", "NotMentioned", FindingType.OMISSION),
    ("P-01", "Contradiction", FindingType.VIOLATION),
    ("P-02", "Entailment", FindingType.VIOLATION),
    ("P-02", "NotMentioned", None),
    ("P-02", "Contradiction", None),
    ("P-03", "Contradiction", FindingType.APPROVAL_NEEDED),
    ("P-03", "NotMentioned", FindingType.OMISSION),  # a missing term is an omission, not a deviation
    ("P-04", "Entailment", FindingType.APPROVAL_NEEDED),
    ("LAW-CA-BPC-16600", "Entailment", FindingType.STATUTORY_RISK),
    ("LAW-CA-BPC-16600", "NotMentioned", None),
    ("LAW-DTSA-1833B", "NotMentioned", FindingType.STATUTORY_RISK),
    ("LAW-DTSA-1833B", "Entailment", None),
])
def test_label_to_finding(rule_id, label, expected):
    r = LAW.get(rule_id) or PACK.rule(rule_id)
    f = finding_from_check(r, res(label), "d1", direction="reverse")
    assert (f.type if f else None) == expected


@pytest.mark.parametrize("rule_id", ["P-01", "P-02", "P-03", "P-04", "LAW-CA-BPC-16600", "LAW-DTSA-1833B"])
@pytest.mark.parametrize("label", ["Entailment", "Contradiction", "NotMentioned"])
def test_reviewer_and_gold_agree_on_finding_types(rule_id, label):
    """For every rule kind and label, the type the reviewer reports is the type gold expects."""
    from counselcopilot.benchmark.gold import anchored_status

    r = LAW.get(rule_id) or PACK.rule(rule_id)
    f = finding_from_check(r, res(label), "d1", direction="reverse")
    g = anchored_status(r, NLILabel(label), (1,))
    assert (f.type if f else None) == (g.type if g else None)


def test_finding_type_helper():
    assert finding_type(PACK.rule("P-01"), violation=False) == FindingType.OMISSION
    assert finding_type(PACK.rule("P-03"), violation=True) == FindingType.APPROVAL_NEEDED
    assert finding_type(LAW["LAW-DTSA-1833B"], violation=False) == FindingType.STATUTORY_RISK


def test_forward_path_may_not_report_omissions():
    assert finding_from_check(PACK.rule("P-01"), res("NotMentioned"), "d1", direction="forward",
                              allow_omission=False) is None


def test_failed_check_is_no_finding():
    bad = CheckResult("NotMentioned", [], 0.0, error="timeout")
    assert finding_from_check(PACK.rule("P-01"), bad, "d1", direction="reverse") is None


def test_finding_cites_rule_clause_and_severity():
    f = finding_from_check(PACK.rule("P-02"), res("Entailment", (4,)), "d1", direction="two_way")
    assert (f.rule_id, f.evidence, f.direction, f.draft_id) == ("P-02", [4], "two_way", "d1")
    assert f.severity == "medium" and f.explanation == "why"


# ------------------------------------------------------------------ ledger

def fnd(rule_id="P-01", t=FindingType.VIOLATION, conf=0.5, ev=(1,)) -> Finding:
    return Finding(draft_id="d", rule_id=rule_id, type=t, confidence=conf, evidence=list(ev))


def test_ledger_keeps_one_finding_per_rule_and_type():
    led = Ledger()
    led.extend([fnd(conf=0.4), fnd(conf=0.8), fnd(t=FindingType.OMISSION, ev=())])
    assert len(led) == 2
    assert [f.confidence for f in led.all() if f.type == FindingType.VIOLATION] == [0.8]


def test_ledger_merges_cited_evidence_when_a_more_confident_finding_arrives():
    led = Ledger()
    led.extend([fnd(conf=0.4, ev=(1,)), fnd(conf=0.8, ev=(3,))])
    assert led.all()[0].evidence == [1, 3]


@pytest.mark.xfail(strict=True, reason="BUG: Ledger.add drops the evidence of a less confident duplicate, so the "
                                        "union of citations depends on the order findings arrive in")
def test_ledger_evidence_union_does_not_depend_on_order():
    led = Ledger()
    led.extend([fnd(conf=0.8, ev=(3,)), fnd(conf=0.4, ev=(1,))])
    assert led.all()[0].evidence == [1, 3]


def test_ledger_is_sorted_and_thread_safe():
    from concurrent.futures import ThreadPoolExecutor

    led = Ledger()
    with ThreadPoolExecutor(8) as ex:
        list(ex.map(lambda i: led.add(fnd(rule_id=f"P-{i % 10:02d}", conf=i / 100)), range(100)))
    ids = [f.rule_id for f in led.all()]
    assert ids == sorted(ids) and len(ids) == 10
    assert all(f.confidence >= 0.9 for f in led.all())
