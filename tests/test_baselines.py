"""Proposal §7 RQ1 baselines: B1 long context, B2 naive RAG, B2+checklist, B3 single agent."""

from __future__ import annotations

import json

from conftest import KeywordLLM, make_law_pack, make_pack
from counselcopilot.baselines.common import QuoteMapper, load_policy_docs, policy_dir_for
from counselcopilot.baselines.systems import B1_SYSTEM, B2_SYSTEM, LongContext, NaiveRAG, NaiveRAGChecklist, SingleAgent, chunk_words
from counselcopilot.data.draft import Draft
from counselcopilot.llm import FakeClient
from counselcopilot.policy.schema import DealContext

DRAFT = Draft("t", ["NON-DISCLOSURE AGREEMENT",
                    "The Recipient shall not solicit or hire the other party's employees for twelve months.",
                    "This Agreement is governed by the laws of Delaware."])
DEAL = DealContext(company="TestCo", counterparty_type="customer", personal_data=False, governing_law="delaware")
DOCS = [("Vendor Policy", "Section 4.2. Vendors must give it back. " + "Filler words about travel. " * 60)]


def answering(findings):
    return FakeClient(lambda req: json.dumps({"findings": findings}))


def test_quote_mapper_maps_prose_quotes_to_rule_ids():
    m = QuoteMapper(make_pack())
    assert m.rule_for("Vendor Policy", "Vendors must give it back.") == "P-01"
    assert m.rule_for("", "Customer NDAs must not contain a non-solicitation clause.") == "P-03"  # via the rule text
    assert m.rule_for("", "Something about travel expenses") is None


def test_b1_sends_one_prompt_with_policies_law_and_nda_and_maps_findings():
    llm = answering([{"document": "Vendor Policy", "quote": "Vendors must give it back.", "type": "omission",
                      "evidence": [1], "explanation": "no return clause"},
                     {"rule_id": "LAW-PENALTY", "type": "violation", "evidence": [2, 99], "explanation": "x"},
                     {"quote": "unrelated words entirely", "type": "violation", "evidence": [], "explanation": "y"}])
    res = LongContext(llm, make_pack(), make_law_pack(), DOCS).review(DRAFT, DEAL)
    assert len(llm.requests) == 1 and llm.requests[0].messages[0].content == B1_SYSTEM
    prompt = llm.requests[0].messages[-1].content
    assert "Vendors must give it back" in prompt and "LAW-DTSA-1833B" in prompt and "[2] This Agreement" in prompt
    got = {(f.rule_id, f.type.value, tuple(f.evidence)) for f in res.findings}
    assert ("P-01", "omission", ()) in got  # an omission cites nothing
    assert ("LAW-PENALTY", "statutory_risk", (2,)) in got  # law ids become statutory risks; bad segment dropped
    assert any(r.startswith("PROSE-") for r, _, _ in got)  # unmappable: counts as a false alarm


def test_b1_without_prose_lists_the_rules():
    llm = answering([])
    LongContext(llm, make_pack()).review(DRAFT, DEAL)
    assert "[P-03]" in llm.requests[0].messages[-1].content


def test_b2_is_forward_only_and_chunks_policy_prose():
    assert all(len(c.split()) <= 150 for c in chunk_words(DOCS[0][1]))
    llm = answering([{"quote": "Customer NDAs must not contain a non-solicitation clause.", "type": "violation",
                      "evidence": [1], "explanation": ""},
                     {"quote": "Vendors must give it back.", "type": "omission", "evidence": [], "explanation": ""}])
    res = NaiveRAG(llm, make_pack(), None, None, window=3).review(DRAFT, DEAL)
    assert {f.type.value for f in res.findings} == {"violation"}
    assert all(r.messages[0].content == B2_SYSTEM for r in llm.requests)


def test_b2_checklist_adds_a_whole_nda_check_of_every_rule():
    res = NaiveRAGChecklist(KeywordLLM(), make_pack(), None, None).review(DRAFT, DEAL)
    keys = {(f.rule_id, f.type.value) for f in res.findings}
    assert ("P-01", "omission") in keys  # P-01 does not apply to customers: no filter, so a false alarm
    assert ("P-03", "violation") in keys


def test_b3_is_one_tool_agent_and_never_sends():
    steps = iter([
        {"thought": "", "action": "list_rules", "args": {}},
        {"thought": "", "action": "search_nda", "args": {"query": "solicit"}},
        {"thought": "", "action": "send_to_counterparty", "args": {"approval_id": "x", "message": "done"}},
        {"thought": "", "action": "finish", "args": {"findings": [
            {"rule_id": "P-03", "type": "violation", "evidence": [1], "explanation": "non-solicit"}]}},
    ])
    llm = FakeClient(lambda req: json.dumps(next(steps)))
    agent = SingleAgent(llm, make_pack(), make_law_pack())
    res = agent.review(DRAFT, DEAL)
    assert [(f.rule_id, f.type.value) for f in res.findings] == [("P-03", "violation")]
    assert [c.status for c in agent.last_calls] == ["ok", "ok", "blocked"]
    assert agent.last_calls[2].attempted_unsafe


def test_shipped_packs_have_prose_for_b1_and_b2():
    d = policy_dir_for("packs/policynda/saas/gold_rules.yaml")
    assert d is not None and len(load_policy_docs(d)) >= 5
