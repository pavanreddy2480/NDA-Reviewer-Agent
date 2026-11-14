"""Proposal §4 Figure 3 (RQ2): opposing counsel, repairer, regression checker, the loop and its
baselines R1, R1+A and R2."""

from __future__ import annotations

import json

import pytest

from conftest import KeywordLLM, RETURN_TERM, make_pack
from counselcopilot.data.draft import Draft, Edit
from counselcopilot.llm import FakeClient
from counselcopilot.policy.schema import DealContext, PolicyPack
from counselcopilot.repair.attacker import ATTACK_SYSTEM, OpposingCounsel, Scenario, loophole_scores, verify_scenario
from counselcopilot.repair.loop import RedTeamRepairLoop, field_conflicts, one_shot, self_refine
from counselcopilot.repair.repairer import (CRITIQUE_SYSTEM, Problem, Repairer, edit_size, problems_from_findings,
                                            validate_edits)
from counselcopilot.review.findings import Finding, FindingType

DRAFT = Draft("r", [
    "NON-DISCLOSURE AGREEMENT",
    "Confidential Information includes information disclosed orally.",
    "Nothing restricts the Recipient from using information retained in the unaided memory of its personnel.",
    "This Agreement is governed by the laws of Delaware.",
])
DEAL = DealContext(company="TestCo", counterparty_type="vendor", personal_data=False, governing_law="delaware")
OMISSION = Finding(draft_id="r", rule_id="P-01", type=FindingType.OMISSION, direction="reverse")
RULES = list(make_pack().rules)


def scen(**kw):
    base = dict(id="S-1", obligation_avoided="x", segments=[2], quotes=["unaided memory"], how="h", loophole_type="residuals")
    return Scenario(**{**base, **kw})


# ------------------------------------------------------------------ attacker

def test_scenarios_must_quote_the_cited_segments():
    assert verify_scenario(DRAFT, scen()).verified
    assert not verify_scenario(DRAFT, scen(quotes=["shall pay a penalty"])).verified
    assert not verify_scenario(DRAFT, scen(segments=[9])).verified
    assert not verify_scenario(DRAFT, scen(quotes=[])).verified


def test_attacker_skips_known_scenarios_and_keeps_rejected_ones_for_the_record():
    reply = {"scenarios": [
        {"obligation_avoided": "use limits", "segments": [2], "quotes": ["unaided memory"], "how": "", "loophole_type": "residuals"},
        {"obligation_avoided": "made up", "segments": [1], "quotes": ["penalty of $1m"], "how": "", "loophole_type": "other"}]}
    att = OpposingCounsel(FakeClient(lambda r: json.dumps(reply)))
    first = att.attack(DRAFT, DEAL)
    assert [s.verified for s in first] == [True, False]
    again = att.attack(DRAFT, DEAL, known=[first[0]])
    assert again[0].verified is False and again[0].reject_reason == "already known"


def test_loophole_scores_match_type_and_segment():
    gold = [{"topic": "residuals", "origin": "planted", "evidence": [2]}, {"hypothesis": "nda-3", "origin": "natural", "evidence": [1]}]
    s = verify_scenario(DRAFT, scen())
    m = loophole_scores([s], gold)
    assert m["recall"] == 0.5 and m["precision"] == 1.0


# ------------------------------------------------------------------ repairer

def problems():
    return problems_from_findings([OMISSION], {r.id: r for r in RULES})


def test_edit_validation_enforces_repair_discipline():
    raw = [{"op": "insert_after", "segment": 3, "text": RETURN_TERM, "fixes": "P-01"},
           {"op": "delete", "segment": 7, "text": "", "fixes": "P-01"},  # no such segment
           {"op": "replace", "segment": 1, "text": "Whatever you like here now.", "fixes": "nothing"},  # no problem
           {"op": "replace", "segment": 1, "text": "", "fixes": "P-01"},  # no text
           {"op": "teleport", "segment": 1, "text": "x", "fixes": "P-01"}]
    edits, dropped = validate_edits(raw, DRAFT, problems())
    assert edits == [Edit("insert_after", 3, RETURN_TERM, "P-01")] and len(dropped) == 4


def test_a_rewrite_that_keeps_nothing_becomes_an_insertion():
    long = Draft("l", ["The Receiving Party shall hold all information of the Disclosing Party in strict confidence "
                       "and shall not disclose it to anyone at all."])
    p = [Problem("P-01", "finding", "x")]
    edits, _ = validate_edits([{"op": "replace", "segment": 0, "text": "Return or destroy everything on request now.",
                                "fixes": "P-01"}], long, p)
    assert edits[0].op == "insert_after"


def test_edit_size_counts_words():
    assert edit_size(DRAFT, [Edit("insert_after", 3, "one two three", "P-01")]) == {"segments": 1, "words": 3}


# ------------------------------------------------------------------ loop

class ScriptedRepairer(Repairer):
    """Inserts the return clause for P-01; deletes cited segments for scenarios."""

    def __init__(self):
        super().__init__(FakeClient())
        self.calls = 0

    def repair(self, draft, problems, one_shot=False, tag="repairer"):
        self.calls += 1
        out = []
        for p in problems:
            if p.id == "P-01":
                out.append(Edit("insert_after", len(draft.segments) - 1, "On request the Receiving Party shall return or destroy all information.", "P-01"))
            elif p.kind == "scenario":
                out.append(Edit("delete", p.evidence[0], "", p.id))
        return out, []


def detector_from(llm):
    from counselcopilot.review.policy_reviewer import PolicyReviewer, ReviewConfig

    cfg = ReviewConfig.preset("full")
    cfg.max_workers = 1
    rev = PolicyReviewer(llm, PolicyPack(company="TestCo", rules=[make_pack().rule("P-01")]), cfg)
    return lambda d, deal: rev.review(d, deal).findings


def test_loop_fixes_attacks_and_stops_clean():
    att_reply = {"scenarios": [{"obligation_avoided": "use limits", "segments": [2], "quotes": ["unaided memory"],
                                "how": "", "loophole_type": "residuals"}]}
    attacker = OpposingCounsel(FakeClient(lambda r: json.dumps(att_reply)))
    loop = RedTeamRepairLoop(ScriptedRepairer(), detector_from(KeywordLLM()), attacker, RULES)
    res = loop.run(DRAFT, DEAL, [OMISSION])
    assert res.stopped == "clean"
    assert not any("unaided memory" in s for s in res.final.segments)
    assert any("return or destroy" in s for s in res.final.segments)
    assert res.rounds[0].fixed == ["P-01:omission"] and res.rounds[0].new == []


def test_loop_without_regression_check_trusts_the_repairer():
    loop = RedTeamRepairLoop(ScriptedRepairer(), None, None, RULES)
    res = loop.run(DRAFT, DEAL, [OMISSION])
    assert res.rounds[0].fixed == ["P-01:omission"] and res.stopped == "clean"


class NoopRepairer(Repairer):
    def __init__(self):
        super().__init__(FakeClient())

    def repair(self, draft, problems, one_shot=False, tag="repairer"):
        return [Edit("insert_after", 0, "Each party bears its own costs in connection with this Agreement.", problems[0].id)], []


def test_loop_stops_stuck_when_a_round_changes_nothing_and_escalates():
    loop = RedTeamRepairLoop(NoopRepairer(), detector_from(KeywordLLM()), None, RULES)
    res = loop.run(DRAFT, DEAL, [OMISSION])
    assert res.stopped == "stuck" and len(res.rounds) == 1
    assert res.escalations and res.escalations[0]["problem"] == "P-01:omission"


def test_impossible_min_max_pair_is_escalated_not_repaired():
    rules = [r.model_copy(update={"constraint": r.constraint.model_copy(update={"value": 72})}) if r.id == "P-04" else r
             for r in RULES]
    conf = field_conflicts(rules, DEAL.model_copy(update={"personal_data": True}))
    assert conf and set(conf[0]["rules"]) == {"P-04", "P-06"}
    f = Finding(draft_id="r", rule_id="P-04", type=FindingType.VIOLATION, direction="field")
    res = RedTeamRepairLoop(ScriptedRepairer(), None, None, rules).run(DRAFT, DEAL.model_copy(update={"personal_data": True}), [f])
    assert any(e["reason"] == "conflict" for e in res.escalations)


def test_token_budget_stops_the_loop():
    from counselcopilot.llm.base import user

    llm = KeywordLLM()

    def detector(d, deal):  # the regression check spends tokens and finds nothing
        llm.complete([user("check the draft")], tag="detector")
        return []

    loop = RedTeamRepairLoop(ScriptedRepairer(), detector, None, RULES, token_budget=1, clients=[llm])
    res = loop.run(DRAFT, DEAL, [OMISSION])
    assert res.stopped == "budget" and len(res.rounds) == 1 and res.tokens >= 1


# ------------------------------------------------------------------ baselines

def test_r1_one_shot_and_r1_with_attacker():
    r1 = one_shot(ScriptedRepairer(), DRAFT, [OMISSION], RULES)
    assert r1.system == "r1" and len(r1.rounds) == 1 and len(r1.edits) == 1
    att = OpposingCounsel(FakeClient(lambda r: json.dumps({"scenarios": [
        {"obligation_avoided": "u", "segments": [2], "quotes": ["unaided memory"], "how": "", "loophole_type": "residuals"}]})))
    r1a = one_shot(ScriptedRepairer(), DRAFT, [OMISSION], RULES, att, DEAL)
    assert len(r1a.edits) == 2 and r1a.scenarios


def test_r2_self_refine_iterates_on_its_own_critique():
    critiques = iter([{"remaining": [{"id": "P-01", "problem": "still missing", "segments": []}], "done": False},
                      {"remaining": [], "done": True}])

    class Critic(ScriptedRepairer):
        def critique(self, draft, problems, tag="self_critique"):
            out = next(critiques)
            return [Problem(r["id"], "critique", r["problem"]) for r in out["remaining"]], out["done"]

    rep = Critic()
    res = self_refine(rep, DRAFT, [OMISSION], RULES)
    assert res.system == "r2_self_refine" and len(res.rounds) == 2 and res.stopped == "clean"


def test_repairer_critique_parses_the_model_reply():
    llm = FakeClient(lambda r: json.dumps({"remaining": [{"id": "P-01", "problem": "x", "segments": [1, 50]}], "done": False}))
    rem, done = Repairer(llm).critique(DRAFT, problems())
    assert rem[0].evidence == [1] and done is False and llm.requests[0].messages[0].content == CRITIQUE_SYSTEM


@pytest.mark.parametrize("system", ["r1", "r1_attacker", "r2", "loop", "loop_no_attacker", "loop_no_regression", "loop_1_round"])
def test_every_rq2_system_runs_on_the_heuristic_backend(system):
    from counselcopilot.experiments.rq2 import make_system
    from counselcopilot.llm.heuristic import HeuristicClient

    llm = HeuristicClient()
    run = make_system(system, Repairer(llm), OpposingCounsel(llm), detector_from(llm), RULES, 3, None, [llm])
    res = run(DRAFT, DEAL, [OMISSION])
    assert res.final is not None and res.tokens >= 0
    if system in ("loop", "r1_attacker", "loop_1_round", "loop_no_regression"):
        assert any(s.verified and s.loophole_type == "residuals" for s in res.scenarios)
