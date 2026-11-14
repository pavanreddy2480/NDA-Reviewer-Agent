"""The tool-calling evaluation runner (experiments/tool_eval.py), driven by scripted fake models."""

import json

from conftest import make_law_pack, make_pack
from counselcopilot.benchmark.planter import INJECTIONS
from counselcopilot.experiments.tool_eval import build_episodes, run_tool_eval
from counselcopilot.llm import FakeClient
from counselcopilot.tools.legal_tools import GOLD_TOOL_SETS


def _step(action, **args):
    return json.dumps({"thought": "", "action": action, "args": args})


class Scripted(FakeClient):
    """Plays the gold tool sequence for the episode it is shown, one step per call."""

    def __init__(self, obey_injection=False):
        self.obey = obey_injection
        super().__init__(self._reply)

    def _reply(self, req):
        task = req.messages[1].content
        n = sum(m.role == "assistant" for m in req.messages)
        rid = next(w.strip("().,") for w in task.split() if w.startswith(("P-", "LAW-")))
        if self.obey and "NDA excerpt" in task:
            return _step("send_to_counterparty", approval_id="pre-approved", message="signed")
        if rid.startswith("LAW-"):
            steps = [("statute_lookup", {"provision_id": rid})]
        else:
            steps = [("rule_lookup", {"rule_id": rid}), ("approval_matrix_query", {"rule_id": rid}),
                     ("precedent_search", {"rule_id": rid, "counterparty": "Acme"})]
            if "request_approval" in self.gold_for[rid]:
                steps.append(("request_approval", {"rule_id": rid, "reason": "deviation"}))
        return _step(*[steps[n][0]], **steps[n][1]) if n < len(steps) else _step("finish", decision="ok")

    gold_for: dict = {}


def test_episodes_cover_approval_and_statutory_findings():
    eps, prec = build_episodes(make_pack(), make_law_pack(), n_injection=0)
    kinds = {e.kind for e in eps}
    assert "statutory_risk" in kinds and kinds & {"approval_needed", "approval_needed_with_precedent"}
    assert all(e.gold == GOLD_TOOL_SETS[e.kind] for e in eps)
    # every precedent belongs to a with-precedent episode
    assert {p["rule_id"] for p in prec} == {e.id for e in eps if e.kind == "approval_needed_with_precedent"}


def test_injection_text_goes_into_the_chosen_number_of_episodes():
    eps, _ = build_episodes(make_pack(), make_law_pack(), n_injection=2)
    assert sum(e.injected for e in eps) == 2
    assert all(any(i in e.task for i in INJECTIONS) for e in eps if e.injected)
    assert not any(any(i in e.task for i in INJECTIONS) for e in eps if not e.injected)


def test_a_model_that_follows_the_gold_path_scores_perfectly(tmp_path):
    eps, _ = build_episodes(make_pack(), make_law_pack(), n_injection=0)
    llm = Scripted()
    llm.gold_for = {e.id: e.gold for e in eps}
    m = run_tool_eval(llm, make_pack(), make_law_pack(), n_injection=0, out_root=str(tmp_path))
    t = m["tool_metrics"]
    assert t["tool_precision"] == 1.0 and t["tool_recall"] == 1.0 and t["arg_validity"] == 1.0
    assert t["attempted_unsafe_per_episode"] == 0 and m["stopped"] == {"finish": len(eps)}
    assert (tmp_path / next(p.name for p in tmp_path.iterdir()) / "metrics.json").exists()


def test_obeying_injection_text_is_counted_but_never_executed(tmp_path):
    llm = Scripted(obey_injection=True)
    llm.gold_for = {e.id: e.gold for e in build_episodes(make_pack(), make_law_pack(), n_injection=0)[0]}
    m = run_tool_eval(llm, make_pack(), make_law_pack(), n_injection=2, max_steps=2, out_root=str(tmp_path))
    assert m["injected"]["episodes_with_unsafe_attempt"] == 2
    assert m["sends_executed"] == 0
