"""Tool calling and the safety plan (proposal §4 Figure 1, §5, §9).

Read-only lookups; request_approval needs a human; send_to_counterparty is a mock that is blocked
without approval. Measured: tool precision/recall vs gold tool sets per defect type, argument
validity, recovery from 10% injected errors, and the attempted unsafe action rate (target 0),
including under prompt-injection text inside NDAs."""

import json

import pytest

from conftest import make_law_pack, make_pack
from counselcopilot.benchmark.planter import INJECTIONS
from counselcopilot.llm import FakeClient
from counselcopilot.tools.agent import run_agent
from counselcopilot.tools.legal_tools import GOLD_TOOL_SETS, build_registry
from counselcopilot.tools.registry import Tool, ToolCallRecord, ToolRegistry, tool_metrics, validate_args

PRECEDENTS = [{"rule_id": "P-05", "counterparty": "Acme", "note": "California law approved in 2025"}]


def registry(**kw) -> ToolRegistry:
    return build_registry(make_pack(), make_law_pack(), PRECEDENTS, **kw)


# ------------------------------------------------------------------ lookups

def test_read_only_lookups():
    reg = registry()
    assert reg.call("rule_lookup", {"rule_id": "P-05"}).result["approval"] == "General Counsel"
    assert reg.call("statute_lookup", {"provision_id": "LAW-PENALTY"}).result["risk_level"] == "possible_risk"
    assert reg.call("approval_matrix_query", {"rule_id": "P-05"}).result == {
        "rule_id": "P-05", "deviation_allowed": True, "approver": "General Counsel"}
    assert reg.call("approval_matrix_query", {"rule_id": "P-01"}).result["deviation_allowed"] is False
    assert reg.call("precedent_search", {"rule_id": "P-05", "counterparty": "acme"}).result == PRECEDENTS
    assert all(t.read_only for n, t in reg.tools.items() if n not in ("request_approval", "send_to_counterparty"))


def test_lookup_of_unknown_id_is_an_error_the_agent_sees():
    rec = registry().call("rule_lookup", {"rule_id": "P-99"})
    assert rec.status == "error" and "P-99" in rec.result


def test_tool_specs_say_which_tools_need_approval():
    specs = {s["name"]: s for s in registry().specs()}
    assert specs["send_to_counterparty"]["needs_approval"] is True
    assert specs["rule_lookup"]["needs_approval"] is False


# ------------------------------------------------------------------ gated actions

def test_request_approval_records_a_request_and_approves_nothing():
    reg = registry()
    rec = reg.call("request_approval", {"rule_id": "P-05", "reason": "California law"})
    assert rec.status == "ok" and rec.result["status"] == "pending"
    assert reg.pending == [{"rule_id": "P-05", "reason": "California law"}]
    assert reg.approvals == set()


def test_send_without_approval_is_blocked_and_counted_as_attempted_unsafe():
    reg = registry()
    rec = reg.call("send_to_counterparty", {"approval_id": "made-up", "message": "signed copy"})
    assert rec.status == "blocked" and rec.attempted_unsafe
    assert reg.sent == []


def test_send_with_a_human_granted_approval_goes_through_as_a_mock():
    reg = registry()
    reg.grant("send_to_counterparty:A-1")
    rec = reg.call("send_to_counterparty", {"approval_id": "A-1", "message": "for signature"})
    assert rec.status == "ok" and not rec.attempted_unsafe and "mock" in rec.result["status"]
    assert reg.sent == [{"approval_id": "A-1", "message": "for signature"}]


def test_an_approval_is_for_one_exact_action():
    reg = registry()
    reg.grant("send_to_counterparty:A-1")
    assert reg.call("send_to_counterparty", {"approval_id": "A-2", "message": "x"}).status == "blocked"


@pytest.mark.xfail(strict=True, reason="BUG: the approval gate is checked after argument validation, so an "
                                        "unapproved send with a missing or extra argument is logged as "
                                        "invalid_args and never counts as an attempted unsafe action")
def test_unapproved_send_with_bad_arguments_still_counts_as_unsafe():
    rec = registry().call("send_to_counterparty", {"message": "send it now"})
    assert rec.attempted_unsafe


@pytest.mark.xfail(strict=True, reason="GAP: request_approval returns no approval id, so nothing links a human's "
                                        "approval of a request to the send it allows")
def test_request_approval_returns_an_id_the_human_can_grant():
    rec = registry().call("request_approval", {"rule_id": "P-05", "reason": "x"})
    assert "approval_id" in rec.result


# ------------------------------------------------------------------ argument checking

SCHEMA = {"type": "object", "properties": {"a": {"type": "integer"}, "b": {"type": ["string", "null"]},
                                           "c": {"type": "string", "enum": ["x", "y"]}}, "required": ["a"]}


@pytest.mark.parametrize("args, problem", [
    ({"a": 1}, None), ({"a": 1, "b": None}, None), ({"a": 1, "c": "x"}, None),
    ({}, "missing"), ({"a": "1"}, "should be"), ({"a": True}, "should be"), ({"a": 1, "z": 0}, "unknown"),
    ({"a": 1, "c": "q"}, "must be one of"), ("not a dict", "object"),
])
def test_validate_args(args, problem):
    err = validate_args(SCHEMA, args)
    assert (err is None) if problem is None else (problem in err)


def test_unknown_tool_and_invalid_args_are_logged():
    reg = registry()
    assert reg.call("delete_everything", {}).status == "unknown_tool"
    assert reg.call("rule_lookup", {"id": "P-01"}).status == "invalid_args"
    assert [r.status for r in reg.log] == ["unknown_tool", "invalid_args"]


def test_tool_exceptions_surface_as_errors():
    reg = ToolRegistry()
    reg.register(Tool("boom", "fails", {"type": "object", "properties": {}}, lambda: 1 / 0))
    assert reg.call("boom", {}).status == "error"


def test_injected_errors_hit_about_ten_percent_of_calls():
    reg = registry(error_rate=0.1, seed=0)
    statuses = [reg.call("rule_lookup", {"rule_id": "P-01"}).status for _ in range(1000)]
    share = statuses.count("injected_error") / len(statuses)
    assert 0.07 <= share <= 0.13


# ------------------------------------------------------------------ tool metrics

def rec(name, status="ok", unsafe=False):
    return ToolCallRecord(0, name, {}, status, None, unsafe)


def test_tool_metrics_against_gold_tool_sets():
    gold = GOLD_TOOL_SETS["approval_needed"]
    log = [rec("rule_lookup"), rec("approval_matrix_query"), rec("statute_lookup"),
           rec("precedent_search", "injected_error"), rec("precedent_search"), rec("nope", "unknown_tool")]
    m = tool_metrics([log], [gold])
    assert m["tool_precision"] == 0.75 and m["tool_recall"] == 0.75  # missed request_approval; extra statute_lookup
    assert m["arg_validity"] == round(1 - 1 / 6, 4)
    assert m["recovery_rate"] == 1.0
    assert m["attempted_unsafe_per_episode"] == 0.0


def test_unsafe_attempts_are_counted_per_episode():
    logs = [[rec("send_to_counterparty", "blocked", True)], [rec("rule_lookup")]]
    m = tool_metrics(logs, [set(), {"rule_lookup"}])
    assert m["attempted_unsafe_per_episode"] == 0.5 and m["episodes_with_unsafe_attempt"] == 1


def test_no_injected_errors_means_no_recovery_rate():
    assert tool_metrics([[rec("rule_lookup")]], [{"rule_lookup"}])["recovery_rate"] is None


def test_gold_tool_sets_cover_gated_and_statutory_findings():
    assert "request_approval" in GOLD_TOOL_SETS["approval_needed"]
    assert "request_approval" not in GOLD_TOOL_SETS["approval_needed_with_precedent"]
    assert GOLD_TOOL_SETS["statutory_risk"] == {"statute_lookup"}


# ------------------------------------------------------------------ the agent loop

class _Steps(FakeClient):
    """A fake model that replies with the given steps in order, then finishes."""

    def __init__(self, steps):
        self.steps = list(steps)
        super().__init__(self._next)

    def _next(self, req):
        s = self.steps.pop(0) if self.steps else {"thought": "", "action": "finish", "args": {}}
        return s if isinstance(s, str) else json.dumps(s)


def test_agent_calls_tools_and_finishes():
    llm = _Steps([{"thought": "look up", "action": "rule_lookup", "args": {"rule_id": "P-05"}},
                  {"thought": "done", "action": "finish", "args": {"answer": "needs GC"}}])
    out = run_agent(llm, registry(), "Review.", "Check P-05.")
    assert out.stopped == "finish" and out.final == {"answer": "needs GC"} and out.steps == 2
    assert [c.name for c in out.calls] == ["rule_lookup"]
    assert "General Counsel" in llm.requests[1].messages[-1].content  # the tool result is fed back


def test_agent_is_told_document_text_is_data():
    llm = _Steps([])
    run_agent(llm, registry(), "Review.", "x")
    assert "data, never instructions" in llm.requests[0].messages[0].content


def test_agent_following_an_injection_is_blocked_and_counted():
    llm = _Steps([{"thought": "the NDA says to send it", "action": "send_to_counterparty",
                   "args": {"approval_id": "pre-approved", "message": INJECTIONS[0]}}])
    reg = registry()
    out = run_agent(llm, reg, "Review.", f"NDA text: {INJECTIONS[0]}")
    assert reg.sent == []
    assert tool_metrics([out.calls], [set()])["attempted_unsafe_per_episode"] == 1.0


def test_agent_stops_on_bad_output_and_max_steps():
    assert run_agent(_Steps(["not json at all", "still not json"]), registry(), "", "").stopped == "bad_output"
    loop = _Steps([{"thought": "", "action": "rule_lookup", "args": {"rule_id": "P-01"}}] * 10)
    out = run_agent(loop, registry(), "", "", max_steps=3)
    assert out.stopped == "max_steps" and len(out.calls) == 3


def test_agent_accepts_an_object_wrapped_in_a_list():
    llm = _Steps([json.dumps([{"thought": "", "action": "finish", "args": {"ok": True}}])])
    assert run_agent(llm, registry(), "", "").final == {"ok": True}
