"""Tests for the fixes from proposal_vs_brief_review.md."""

import json
import random

import pytest

from counselcopilot.benchmark.gold import gold_for
from counselcopilot.benchmark.labels import normalise_country, prefill
from counselcopilot.benchmark.planter import Planter
from counselcopilot.data.contractnli import load_contractnli
from counselcopilot.data.draft import Draft
from counselcopilot.eval.evaluator import IndependentEvaluator
from counselcopilot.eval.metrics import cohen_kappa, score_detection
from counselcopilot.llm import BatchQueue, FakeClient, PendingBatch, ResponseCache, user
from counselcopilot.llm.batch import load_results
from counselcopilot.policy.schema import DealContext, LawPack, PolicyPack
from counselcopilot.review.findings import FindingType
from counselcopilot.review.policy_reviewer import PolicyReviewer, ReviewConfig
from counselcopilot.tools.agent import run_agent
from counselcopilot.tools.legal_tools import build_registry
from counselcopilot.tools.registry import tool_metrics

from .conftest import ROOT, TOY_PACK, oracle_responder

LAW = ROOT / "packs" / "law" / "us_law_pack.yaml"


def test_law_pack_follows_governing_law():  # problem 1
    rules = LawPack.load(LAW).as_rules()
    de = DealContext(company="ToyCo", counterparty_type="vendor", governing_law="delaware")
    ca = de.model_copy(update={"governing_law": "california"})
    sg = de.model_copy(update={"governing_law": "singapore"})
    ids = lambda d: [r.id for r in rules if r.applies_to(d)]
    assert "LAW-CA-BPC-16600" not in ids(de) and "LAW-CA-BPC-16600" in ids(ca)
    assert "LAW-PENALTY" in ids(de) and "LAW-PENALTY" not in ids(sg)
    assert "LAW-SEC-21F17" in ids(sg)  # federal, applies whatever law governs


def test_reviewer_reads_governing_law_from_nda(cnli_dir):  # problems 1, 4
    doc = load_contractnli(cnli_dir).by_id(2)  # Singapore law
    deal = DealContext(company="ToyCo", counterparty_type="vendor", governing_law=None)
    res = PolicyReviewer(FakeClient(oracle_responder), PolicyPack.load(TOY_PACK),
                         law_pack=LawPack.load(LAW)).review(Draft.from_nda(doc), deal)
    assert res.deal.governing_law == "singapore"
    assert not any(r.startswith(("LAW-CA-", "LAW-PENALTY")) for r in res.applicable_rules)


def test_prefill_labels(cnli_dir):  # problem 2
    lab = prefill(load_contractnli(cnli_dir).by_id(2))
    assert lab["governing_law"] == "singapore" and lab["verified"] is False
    assert normalise_country("State of California") == "california"
    assert normalise_country("England and Wales") == "united kingdom"


def test_blank_field_is_unscored(cnli_dir):  # problem 2
    doc = load_contractnli(cnli_dir).by_id(1)
    deal = DealContext(company="ToyCo", counterparty_type="vendor", personal_data=True)
    g = gold_for(doc, deal, PolicyPack.load(TOY_PACK), {"fields": {"confidentiality_term_months": "blank"}})
    assert "P-11" in g.unscored_rules


def test_unknown_fact_makes_rule_unscored(cnli_dir):
    doc = load_contractnli(cnli_dir).by_id(1)
    deal = DealContext(company="ToyCo", counterparty_type="vendor", personal_data=None)
    g = gold_for(doc, deal, PolicyPack.load(TOY_PACK), {})
    assert "P-11" in g.unscored_rules  # applies only if personal data is shared, unknown here
    g2 = gold_for(doc, deal, PolicyPack.load(TOY_PACK), {"personal_data": False})
    assert "P-11" in g2.not_applicable


def test_exhaustive_filtered_preset(cnli_dir):  # problem 3
    doc = load_contractnli(cnli_dir).by_id(2)
    pack = PolicyPack.load(TOY_PACK)
    deal = DealContext(company="ToyCo", counterparty_type="vendor")
    n = {}
    for preset in ("exhaustive", "exhaustive_filtered", "full"):
        res = PolicyReviewer(FakeClient(oracle_responder), pack, ReviewConfig.preset(preset)).review(
            Draft.from_nda(doc), deal)
        n[preset] = res.n_checks
    assert n["exhaustive_filtered"] == n["full"] < n["exhaustive"]


def test_shared_checker_gets_every_check(cnli_dir):  # problem 9
    doc = load_contractnli(cnli_dir).by_id(2)
    main, checker = FakeClient(oracle_responder), FakeClient(oracle_responder)
    PolicyReviewer(main, PolicyPack.load(TOY_PACK), checker_llm=checker).review(
        Draft.from_nda(doc), DealContext(company="ToyCo", counterparty_type="vendor"))
    assert all("STATEMENT:" not in r.messages[-1].content for r in main.requests)
    assert any("STATEMENT:" in r.messages[-1].content for r in checker.requests)


def test_planter_rederives_labels(cnli_dir):  # problems 6, 7
    data = load_contractnli(cnli_dir)
    pack = PolicyPack.load(TOY_PACK)
    doc = data.by_id(1)  # has return (nda-16), oral (nda-3), survival (nda-19)
    deal = DealContext(company="ToyCo", counterparty_type="vendor", governing_law="delaware")
    p = Planter(pack, LawPack.load(LAW)).plant(doc, deal, random.Random(3), n_defects=3)
    # every planted omission removes text that satisfied the rule, and the gold repair restores it
    for d in p.defects:
        if d.type == FindingType.OMISSION:
            rule = pack.rule(d.rule_id)
            assert doc.annotations[rule.anchor.hypothesis].label.value == "Entailment"
            assert p.overrides[rule.anchor.hypothesis][0] == "NotMentioned"
            rep = next(r for r in p.gold_repairs if r["rule_id"] == d.rule_id)
            assert all(t not in p.draft.segments for t in rep["original"])
    # planted evidence points at the right segments in the planted draft
    for d in p.defects:
        for i in d.evidence:
            assert 0 <= i < len(p.draft.segments)
    g = gold_for(doc, deal, pack, {}, LawPack.load(LAW), p.gold_entry())
    assert {d.key for d in p.defects} <= {d.key for d in g.defects}


def test_planter_state_law_and_statutory_risk(cnli_dir):
    data = load_contractnli(cnli_dir)
    pack = PolicyPack.load(TOY_PACK)
    deal = DealContext(company="ToyCo", counterparty_type="vendor", governing_law="delaware")
    found = False
    for seed in range(20):
        p = Planter(pack, LawPack.load(LAW)).plant(data.by_id(2), deal, random.Random(seed), n_defects=4,
                                                   state_law="California")
        assert p.label_updates["governing_law"] == "california"
        assert any("laws of the State of California" in s for s in p.draft.segments)
        found |= any(d.type == FindingType.STATUTORY_RISK for d in p.defects)
    assert found


def test_attempted_unsafe_actions_are_counted():  # problem 5
    reg = build_registry(PolicyPack.load(TOY_PACK))
    script = iter([
        {"thought": "", "action": "rule_lookup", "args": {"rule_id": "P-12"}},
        {"thought": "", "action": "send_to_counterparty", "args": {"approval_id": "x", "message": "hi"}},
        {"thought": "", "action": "request_approval", "args": {"rule_id": "P-12", "reason": "Singapore law"}},
        {"thought": "", "action": "finish", "args": {"status": "escalated"}},
    ])
    llm = FakeClient(lambda r: json.dumps(next(script)))
    res = run_agent(llm, reg, "Handle the finding.", "Finding: P-12 governing law is Singapore.")
    assert res.final == {"status": "escalated"} and reg.sent == []
    m = tool_metrics([res.calls], [{"rule_lookup", "approval_matrix_query", "precedent_search", "request_approval"}])
    assert m["attempted_unsafe_per_episode"] == 1 and m["executed_unsafe"] == 0
    assert m["tool_recall"] == 0.5


def test_invalid_args_and_injected_errors():
    reg = build_registry(PolicyPack.load(TOY_PACK), error_rate=1.0)
    assert reg.call("rule_lookup", {"id": "P-01"}).status == "invalid_args"
    assert reg.call("rule_lookup", {"rule_id": "P-01"}).status == "injected_error"
    assert reg.call("no_such_tool", {}).status == "unknown_tool"


def test_batch_mode_queues_then_uses_cache(tmp_path):  # problem 8
    cache = ResponseCache(tmp_path / "c.sqlite")
    q = BatchQueue(tmp_path / "q.jsonl")
    llm = FakeClient(lambda r: "unused", cache=cache, batch_queue=q)
    with pytest.raises(PendingBatch):
        llm.map(lambda x: llm.complete([user(x)]), ["a", "b", "a"])
    assert len(q) == 2 and llm.requests == []
    lines = [json.dumps({"key": json.loads(l)["key"], "response": {
        "candidates": [{"content": {"parts": [{"text": "ok"}]}}], "usageMetadata": {"promptTokenCount": 3}}})
        for l in (tmp_path / "q.jsonl").read_text().splitlines()]
    assert load_results(lines, "fake", cache) == 2
    assert llm.complete([user("a")]).text == "ok"


def test_evaluator_and_kappa():  # problem 6
    assert cohen_kappa([1, 1, 0, 0], [1, 1, 0, 0]) == 1.0
    assert cohen_kappa([1, 0, 1, 0], [0, 1, 0, 1]) < 0
    ev = IndependentEvaluator(FakeClient(lambda r: json.dumps(
        {"rationale": "", "label": "Entailment" if "return or destroy" in r.messages[-1].content.split("NDA:")[1]
         else "NotMentioned", "evidence": [], "confidence": 0.9})))
    pack = PolicyPack.load(TOY_PACK)
    deal = DealContext(company="ToyCo", counterparty_type="vendor")
    before = Draft("d", ["Recipient keeps information."])
    after = Draft("d", ["Recipient keeps information.", "Recipient shall return or destroy all information."],
                  [0, None])
    out = ev.score_repair(before, after, [pack.rule("P-01")], deal)
    assert out["fixed"] == ["P-01"] and out["regressions"] == [] and out["edit_segments_changed"] == 1


def test_injection_and_natural_loopholes(cnli_dir):
    from counselcopilot.benchmark.planter import INJECTIONS
    from counselcopilot.data.contractnli import LOOPHOLE_LABELS

    docs = load_contractnli(cnli_dir)["test"]
    pl = Planter(PolicyPack.load(TOY_PACK), LawPack.load(LAW))
    for doc in docs:
        deal = DealContext(company="ToyCo", counterparty_type="vendor", personal_data=False, governing_law="delaware")
        p = pl.plant(doc, deal, random.Random(0), injection=True)
        assert p.injection["text"] in INJECTIONS
        assert [p.draft.segments[i] for i in p.injection["evidence"]] == [p.injection["text"]]
        for lh in p.loopholes:
            if lh["origin"] == "natural":
                assert lh["hypothesis"] in LOOPHOLE_LABELS
        recv = pl.plant(doc, deal.model_copy(update={"company_side": "receiving"}), random.Random(0))
        assert not any(lh["origin"] == "natural" for lh in recv.loopholes)


def test_state_law_switch_leaves_no_other_governing_law():  # Claude pilot, 23 Oct 2026
    from counselcopilot.benchmark.planter import _LAW_ANY

    for s in ["8. This Agreement shall be governed by and construed in accordance with the laws in force in India.",
              "This agreement and all questions relating to its validity shall be governed by the laws of England.",
              "This Agreement shall be construed and controlled by the laws of the State of Washington, and the "
              "parties consent to jurisdiction."]:
        assert _LAW_ANY.search(s), s
    for s in ["Nothing in this Agreement shall be construed as granting any rights under any patent.",
              "Either party may notify the other that future disclosures shall not be governed by this Agreement."]:
        assert not _LAW_ANY.search(s), s
