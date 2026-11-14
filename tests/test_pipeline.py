"""Proposal §4 Figure 1: the full detection pipeline and its parts (frames, consistency reviewer,
law reviewer, cross-reference graph, verifier, planner, precedent memory, approval agent)."""

from __future__ import annotations

import json

import pytest

from conftest import KeywordLLM, NONCOMPETE_TERM, make_law_pack, make_pack
from counselcopilot.agents.handoff import ApprovalDesk, handoff_metrics
from counselcopilot.agents.memory import Precedent, PrecedentMemory, scripted_precedents
from counselcopilot.agents.pipeline import CounselCopilot, PipelineConfig
from counselcopilot.agents.planner import Planner
from counselcopilot.data.draft import Draft
from counselcopilot.llm import FakeClient
from counselcopilot.policy.schema import DealContext
from counselcopilot.review.consistency import check_consistency, resolve_cross_ref, term_usages
from counselcopilot.review.findings import Finding, FindingType
from counselcopilot.review.frames import (ObligationFrame, extract_frames, fields_from_frames, frame_field_accuracy,
                                          regex_frames)
from counselcopilot.review.law_reviewer import dispute_risks
from counselcopilot.review.verifier import Verifier
from counselcopilot.review.xref import CrossRefGraph

DRAFT = Draft("t", [
    "MUTUAL NON-DISCLOSURE AGREEMENT",
    '1. "Confidential Information" means information disclosed orally or in writing.',
    "2. The obligations of confidentiality last for two (2) years.",
    "3. This Agreement is governed by the laws of the State of California.",
    "4. Any dispute shall be resolved by the courts of New York.",
    "5. For 24 months the Receiving Party shall not compete with the Disclosing Party.",
    "6. Notices under Section 9 go to the addresses above.",
])


def form(**kw) -> DealContext:
    return DealContext(**{"company": "TestCo", "counterparty_type": "vendor", "personal_data": False,
                          "governing_law": "california", **kw})


# ------------------------------------------------------------------ frames

def test_regex_frames_read_durations_law_and_covenants():
    f = fields_from_frames(regex_frames(DRAFT))
    assert f["confidentiality_term_months"] == (24.0, [2])
    assert f["governing_law"][0] == "california" and f["dispute_forum"][0] == "new york"
    assert f["non_compete"] == (True, [5])


def test_model_frames_fall_back_to_rules_when_the_reply_is_unreadable():
    broken = FakeClient(lambda req: "no json here")
    frames = extract_frames(broken, DRAFT)
    assert frames and all(f.source == "regex" for f in frames)


def test_model_frames_only_keep_segments_that_were_shown():
    reply = {"frames": [{"segment": 2, "clause_type": "confidentiality_term", "party": "each party", "action": "keep",
                         "object": "confidential information", "condition": "", "duration": "3 years", "exception": ""},
                        {"segment": 99, "clause_type": "other", "party": "", "action": "", "object": "", "condition": "",
                         "duration": "", "exception": ""}]}
    frames = extract_frames(FakeClient(lambda req: json.dumps(reply)), DRAFT, [2])
    assert [f.segment for f in frames] == [2] and frames[0].months == 36.0


def test_frame_field_accuracy_compares_durations_as_numbers():
    gold = [ObligationFrame(2, "confidentiality_term", "each party", "keep confidential", "confidential information",
                            "", "two (2) years", "")]
    pred = [ObligationFrame(2, "confidentiality_term", "each party", "keep confidential", "confidential information",
                            "", "24 months", "")]
    m = frame_field_accuracy(gold, pred)
    assert m["field_accuracy"]["duration"] == 1.0 and m["segment_recall"] == 1.0
    assert frame_field_accuracy(gold, [])["mean_field_accuracy"] == 0.0


def test_reviewer_with_frames_needs_no_field_questions():
    from counselcopilot.review.policy_reviewer import PolicyReviewer, ReviewConfig

    llm = KeywordLLM()
    cfg = ReviewConfig.preset("full")
    cfg.frames, cfg.max_workers = True, 1
    PolicyReviewer(llm, make_pack(), cfg).review(DRAFT, form(governing_law="delaware"))
    # frames came back empty from the fake model, so fields fell back to the rule-based parser
    assert not llm.prompts_with("How long do the confidentiality obligations last")


# ------------------------------------------------------------------ consistency and law

def test_consistency_tools():
    assert resolve_cross_ref(DRAFT, "9")["status"] == "missing"
    assert resolve_cross_ref(DRAFT, "3")["status"] == "ok"
    assert term_usages(DRAFT, "Confidential Information")["defined_in"] == [1]
    ids = {f.rule_id for f in check_consistency(DRAFT)}
    assert "CONS-XREF-9" in ids


def test_conflicting_terms_and_double_definitions_are_inconsistencies():
    d = Draft("c", ['"Confidential Information" means business information.',
                    '"Confidential Information" means technical information only.',
                    "The confidentiality obligations last for three (3) years.",
                    "Confidential Information shall be kept confidential for a period of five (5) years."])
    ids = {f.rule_id for f in check_consistency(d)}
    assert "CONS-TERM" in ids and any(i.startswith("CONS-DEF") for i in ids)
    assert all(f.type == FindingType.INCONSISTENCY for f in check_consistency(d))


def test_dispute_risk_forum_mismatch():
    ids = {f.rule_id for f in dispute_risks(DRAFT, "california")}
    assert "RISK-FORUM" in ids


# ------------------------------------------------------------------ cross-reference graph

def test_xref_graph_links_refs_both_ways_and_field_pairs():
    pack = make_pack()
    g = CrossRefGraph(pack.rules)
    assert "P-06" in g.neighbours("P-04") and "P-04" in g.neighbours("P-06")
    assert g.approver("P-05") == "General Counsel" and g.approver("P-01") is None


# ------------------------------------------------------------------ verifier

def test_verifier_structural_checks():
    v = Verifier(FakeClient(), make_pack().rules)
    bad = [Finding(draft_id="t", rule_id="P-99", type=FindingType.VIOLATION, evidence=[1]),
           Finding(draft_id="t", rule_id="P-01", type=FindingType.OMISSION, evidence=[1], direction="reverse"),
           Finding(draft_id="t", rule_id="P-03", type=FindingType.VIOLATION, evidence=[], direction="reverse"),
           Finding(draft_id="t", rule_id="P-03", type=FindingType.VIOLATION, evidence=[42])]
    assert all(v.verify(DRAFT, f).verdict == "unsupported" for f in bad)


def test_verifier_follows_the_model_and_marks_low_confidence_uncertain():
    f = Finding(draft_id="t", rule_id="P-03", type=FindingType.VIOLATION, evidence=[5], direction="reverse")
    ans = lambda verdict, c: FakeClient(lambda req: json.dumps({"rationale": "", "verdict": verdict, "confidence": c}))
    assert Verifier(ans("supported", 0.9), make_pack().rules).verify(DRAFT, f).finding.verified is True
    assert Verifier(ans("unsupported", 0.9), make_pack().rules).verify(DRAFT, f).finding.verified is False
    assert Verifier(ans("supported", 0.2), make_pack().rules).verify(DRAFT, f).verdict == "uncertain"


def test_field_and_tool_findings_skip_the_model_check():
    llm = FakeClient()
    f = Finding(draft_id="t", rule_id="P-04", type=FindingType.VIOLATION, evidence=[2], direction="field")
    assert Verifier(llm, make_pack().rules).verify(DRAFT, f).verdict == "supported" and llm.requests == []


# ------------------------------------------------------------------ planner

def test_planner_never_drops_the_policy_reviewer():
    llm = FakeClient(lambda req: json.dumps({"reviewers": ["law"], "rationale": "x"}))
    assert Planner(llm).plan(DRAFT, form()).reviewers == ["policy", "law"]


def test_planner_runs_everything_on_an_unreadable_reply_and_in_fixed_mode():
    assert Planner(FakeClient(lambda r: "??")).plan(DRAFT, form()).reviewers == ["policy", "law", "consistency"]
    assert Planner(None, "fixed").plan(DRAFT, form(), law_available=False).reviewers == ["policy", "consistency"]


def test_rule_planner_skips_law_for_a_plain_foreign_deal():
    plain = Draft("p", ["The parties shall keep information confidential."] * 3)
    plan = Planner(None, "rules").plan(plain, form(governing_law="united kingdom"))
    assert "law" not in plan.reviewers


# ------------------------------------------------------------------ memory and hand-off

def test_precedent_memory_finds_by_rule_and_counterparty_and_persists(tmp_path):
    m = PrecedentMemory(path=str(tmp_path / "m.json"))
    m.add(Precedent("P-05", "vendor", "General Counsel", value="singapore", company="TestCo"))
    assert m.find("P-05", "Vendor", "TestCo") is not None
    assert m.find("P-05", "customer", "TestCo") is None
    assert m.find("P-05", "vendor", "TestCo", value="england") is None
    assert PrecedentMemory.load(tmp_path / "m.json").find("P-05", "vendor") is not None


def test_scripted_precedents_cover_only_rules_with_an_approval_route():
    ps = scripted_precedents([make_pack()], 10)
    assert ps and {p.rule_id for p in ps} == {"P-05"}


APPROVAL = Finding(draft_id="t", rule_id="P-05", type=FindingType.APPROVAL_NEEDED, evidence=[3], direction="field")


def test_approval_desk_resolves_by_precedent_or_files_a_request():
    mem = PrecedentMemory([Precedent("P-05", "vendor", "General Counsel", company="TestCo")])
    out = ApprovalDesk(FakeClient(), make_pack(), memory=mem, agent=False).handle([APPROVAL], form())
    assert out.resolved and not out.escalations
    out = ApprovalDesk(FakeClient(), make_pack(), agent=False).handle([APPROVAL], form())
    assert out.escalations[0].reason == "approval" and not out.resolved


def test_approval_agent_tool_calls_are_logged_and_scored():
    from counselcopilot.llm.heuristic import HeuristicClient
    from counselcopilot.tools.registry import tool_metrics

    out = ApprovalDesk(HeuristicClient(), make_pack(), agent=True).handle([APPROVAL], form())
    assert out.escalations and out.escalations[0].approval_id.startswith("APR-")
    m = tool_metrics(out.tool_logs, out.gold_sets)
    assert m["tool_recall"] == 1.0 and m["attempted_unsafe_per_episode"] == 0


def test_an_agent_that_tries_to_send_is_blocked_and_counted():
    from counselcopilot.tools.registry import tool_metrics

    step = json.dumps({"thought": "send", "action": "send_to_counterparty", "args": {"approval_id": "x", "message": "y"}})
    out = ApprovalDesk(FakeClient(lambda r: step), make_pack(), agent=True, max_steps=2).handle([APPROVAL], form())
    assert tool_metrics(out.tool_logs, out.gold_sets)["episodes_with_unsafe_attempt"] == 1
    assert out.escalations  # fell back to a plain request


def test_handoff_metrics():
    from counselcopilot.agents.handoff import Escalation

    m = handoff_metrics({1: [Escalation("P-05", "approval_needed", "approval"), Escalation("P-01", "violation", "approval")]},
                        {}, {1: {("P-05", "approval_needed")}})
    assert m["handoff_precision"] == 0.5 and m["handoff_recall"] == 1.0


# ------------------------------------------------------------------ the pipeline

def pipeline(cfg=None, llm=None, memory=None):
    return CounselCopilot(llm or KeywordLLM(fields={"governing_law": "california", "confidentiality_term_months": 24}),
                          make_pack(), make_law_pack(), cfg or PipelineConfig(), memory=memory)


def test_pipeline_runs_every_reviewer_and_keeps_unscored_findings_apart():
    res = pipeline(PipelineConfig.ablation("fixed_pipeline")).review(DRAFT, form())
    keys = {(f.rule_id, f.type.value) for f in res.findings}
    assert ("LAW-CA-BPC-16600", "statutory_risk") in keys  # non-compete under California law
    assert ("P-04", "violation") not in keys  # P-04 needs personal data; this deal has none
    assert all(not f.rule_id.startswith(("CONS-", "RISK-")) for f in res.findings)
    assert {f.rule_id for f in res.unscored_findings} >= {"CONS-XREF-9"}
    assert res.plan.reviewers == ["policy", "law", "consistency"]


def test_pipeline_verifier_drops_unsupported_findings():
    class Rejecting(KeywordLLM):
        def _respond(self, req):
            from counselcopilot.review.verifier import VERIFY_SYSTEM

            if req.messages[0].content == VERIFY_SYSTEM:
                return json.dumps({"rationale": "no", "verdict": "unsupported", "confidence": 0.9})
            return super()._respond(req)

    full = pipeline(llm=Rejecting()).review(DRAFT, form())
    off = pipeline(PipelineConfig.ablation("no_verifier"), llm=Rejecting()).review(DRAFT, form())
    model_checked = lambda r: [f for f in r.findings if f.direction not in ("field", "tool")]
    assert model_checked(off) and not model_checked(full)


def test_pipeline_hands_approval_findings_to_the_desk_and_memory_avoids_escalation():
    d = Draft("g", ["This Agreement is governed by the laws of Singapore."])
    llm = lambda: KeywordLLM(fields={"governing_law": "singapore"})
    fresh = pipeline(llm=llm()).review(d, form(governing_law=None))
    assert any(e.rule_id == "P-05" for e in fresh.handoff.escalations)
    mem = PrecedentMemory([Precedent("P-05", "vendor", "General Counsel", company="TestCo")])
    again = pipeline(llm=llm(), memory=mem).review(d, form(governing_law=None))
    assert any(e.rule_id == "P-05" for e in again.handoff.resolved)
    assert not any(e.rule_id == "P-05" for e in again.handoff.escalations)


@pytest.mark.parametrize("name", PipelineConfig.ABLATIONS)
def test_every_ablation_builds_and_runs(name):
    res = pipeline(PipelineConfig.ablation(name)).review(DRAFT, form())
    assert res.plan is not None


def test_unknown_ablation_is_an_error():
    with pytest.raises(KeyError):
        PipelineConfig.ablation("no_brain")


def test_no_reverse_ablation_reports_no_omissions():
    res = pipeline(PipelineConfig.ablation("no_reverse")).review(Draft("e", ["Each party bears its own costs."]), form())
    assert not [f for f in res.findings if f.type == FindingType.OMISSION]
    res = pipeline().review(Draft("e", ["Each party bears its own costs."]), form())
    assert ("P-01", "omission") in {(f.rule_id, f.type.value) for f in res.findings}


def test_noncompete_term_constant_matches_law_pack():
    assert make_law_pack().provisions[0].risk_pattern == NONCOMPETE_TERM
