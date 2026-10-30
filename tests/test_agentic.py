from pathlib import Path
import json
import re

import pytest

from conftest import KeywordLLM, make_pack
from conftest import deal as make_deal
from counselcopilot.cli import main
from counselcopilot.data.draft import Draft
from counselcopilot.experiments.compare import compare_presets, format_comparison
from counselcopilot.experiments.rq1 import run_rq1
from counselcopilot.llm import BatchQueue, FakeClient, PendingBatch, ResponseCache
from counselcopilot.policy.schema import DealContext, PolicyPack, Rule
from counselcopilot.retrieval.index import HybridIndex, Passage
from counselcopilot.review.agentic import search_evidence
from counselcopilot.review.findings import FindingType
from counselcopilot.review.policy_reviewer import PolicyReviewer, ReviewConfig
from test_contractnli_and_rq1 import data  # noqa: F401  (fixture)

ROOT = Path(__file__).resolve().parents[1]
TOY_PACK = ROOT / "packs" / "toy" / "toy_pack.yaml"

TERM = "Receiving Party shall destroy or return some Confidential Information upon the termination of Agreement."
HIDDEN = 20  # shares no word with the rule, so the fixed search cannot reach it
SEGMENTS = [f"Filler{i} notes item{i}." for i in range(30)]
SEGMENTS[HIDDEN] = "On expiry the recipient must hand back or erase all materials."
DRAFT = Draft("d", SEGMENTS)
DEAL = DealContext(company="T", counterparty_type="vendor", governing_law="delaware")


def pack(kind="require"):
    return PolicyPack(company="T", rules=[Rule(id="P-01", title="Return on termination", requirement=TERM,
                                               term=TERM, kind=kind)])


def step(action, **args):
    return json.dumps({"thought": "", "action": action, "args": args})


def is_agent(req):
    return "TOOLS:" in req.messages[0].content


def checker(req):
    """Entailment when the shown segments hold the hidden clause, else NotMentioned."""
    msg = req.messages[-1].content
    if "hand back" in msg:
        i = int(re.search(r"^\[(\d+)\] On expiry", msg, re.M).group(1))
        return json.dumps({"rationale": "found", "label": "Entailment", "evidence": [i], "confidence": 0.9})
    return json.dumps({"rationale": "absent", "label": "NotMentioned", "evidence": [], "confidence": 0.8})


def smart_agent(req):
    """Searches in other words, then picks what it found."""
    last = req.messages[-1].content
    if last.startswith("RESULT"):
        return step("finish", segments=[int(i) for i in re.findall(r'"segment": (\d+)', last)][:1])
    return step("search_nda", query="hand back erase materials")


def reply(agent, check=checker):
    return lambda req: agent(req) if is_agent(req) else check(req)


def review(llm, preset="agentic", kind="require", cfg_kw=None):
    cfg = ReviewConfig.preset(preset)
    for k, v in (cfg_kw or {}).items():
        setattr(cfg, k, v)
    return PolicyReviewer(llm, pack(kind), cfg).review(DRAFT, DEAL)


def test_agent_clears_a_false_omission():
    assert review(FakeClient(reply(smart_agent)), "full").findings[0].type == FindingType.OMISSION
    res = review(FakeClient(reply(smart_agent)))
    assert res.findings == []
    assert [c.direction for c in res.checks] == ["reverse", "agentic"] and res.n_agent_searches == 1
    assert res.checks[0].agent.queries == ["hand back erase materials"]
    assert set(res.checks[1].result.shown) == {HIDDEN - 1, HIDDEN, HIDDEN + 1}  # keeps the ±1 neighbours


def test_agent_finds_a_buried_forbidden_clause():
    assert review(FakeClient(reply(smart_agent)), "full", "forbid").findings == []
    res = review(FakeClient(reply(smart_agent)), kind="forbid")
    f = res.findings[0]
    assert f.type == FindingType.VIOLATION and f.direction == "agentic" and f.evidence == [HIDDEN]


def test_settled_check_never_starts_an_agent():
    llm = FakeClient(reply(smart_agent, lambda r: json.dumps(
        {"rationale": "", "label": "Entailment", "evidence": [0], "confidence": 0.9})))
    draft = Draft("d", ["The Recipient shall destroy or return Confidential Information upon termination."])
    res = PolicyReviewer(llm, pack(), ReviewConfig.preset("agentic")).review(draft, DEAL)
    assert res.n_agent_searches == 0 and not any(is_agent(r) for r in llm.requests)


def test_low_confidence_label_is_unsettled():
    llm = FakeClient(reply(lambda r: step("finish", segments=[]), lambda r: json.dumps(
        {"rationale": "", "label": "Entailment", "evidence": [0], "confidence": 0.3})))
    draft = Draft("d", ["The Recipient shall destroy or return Confidential Information upon termination."])
    res = PolicyReviewer(llm, pack(), ReviewConfig.preset("agentic")).review(draft, DEAL)
    assert res.n_agent_searches == 1


def test_no_new_evidence_means_no_second_check():
    res = review(FakeClient(reply(lambda r: step("finish", segments=[]))))
    assert res.findings[0].type == FindingType.OMISSION and res.findings[0].direction == "reverse"
    assert res.n_checks == 1 and res.n_agent_searches == 1


def test_out_of_steps_keeps_what_the_searches_found():
    res = review(FakeClient(reply(lambda r: step("search_nda", query="hand back"))),
                 cfg_kw={"agentic_max_steps": 2})
    assert res.checks[0].agent.stopped == "max_steps" and res.checks[0].agent.segments == [HIDDEN]
    assert res.findings == []


def _search(agent, shown):
    index = HybridIndex([Passage(str(i), s) for i, s in enumerate(SEGMENTS)])
    return search_evidence(FakeClient(agent), pack().rules[0], "q", DRAFT, index, shown)


def test_search_hides_segments_already_checked():
    assert _search(reply(smart_agent), [HIDDEN]).segments == []


def test_agent_cannot_pick_segments_no_tool_returned():
    assert _search(lambda r: step("finish", segments=[3, 99, "x", True]), []).segments == []


def test_failed_second_check_keeps_the_first_result():
    def broken(req):
        raise RuntimeError("backend down")

    res = review(FakeClient(reply(smart_agent, broken)))
    assert res.findings[0].type == FindingType.OMISSION and res.n_errors == 1


def test_failed_agent_keeps_the_first_result():
    def broken(req):
        raise RuntimeError("schema rejected")

    res = review(FakeClient(reply(broken)))
    assert res.findings[0].type == FindingType.OMISSION and res.checks[0].agent.stopped == "error"


def test_batch_mode_queues_the_agent(tmp_path):
    llm = FakeClient(reply(smart_agent), cache=ResponseCache(tmp_path / "c.sqlite"),
                     batch_queue=BatchQueue(tmp_path / "q.jsonl"))
    with pytest.raises(PendingBatch):
        review(llm)


def test_presets_without_the_flag_never_search():
    llm = FakeClient(reply(smart_agent))
    assert review(llm, "full").n_agent_searches == 0 and not any(is_agent(r) for r in llm.requests)


def test_compare_shows_the_changed_rule():
    cmp = compare_presets(FakeClient(reply(smart_agent)), pack(), DRAFT, DEAL, ["full", "agentic"])
    assert cmp["differs"] == ["P-01"] and cmp["rules"]["P-01"] == {"full": "omission", "agentic": "-"}
    assert cmp["presets"]["agentic"]["agent_searches"] == 1
    assert cmp["presets"]["agentic"]["tokens"] > cmp["presets"]["full"]["tokens"]
    assert "P-01 *" in format_comparison(cmp)


def test_rq1_agentic_records_the_searches(data, tmp_path):
    class Agentic(KeywordLLM):
        def _respond(self, req):
            return step("finish", segments=[]) if is_agent(req) else super()._respond(req)

    m = run_rq1(Agentic(confidence=0.3), data, [make_pack()], split="test", deals={i: make_deal() for i in (4, 5, 6, 7)},
                preset="agentic", out_root=str(tmp_path), max_workers=1)
    assert m["agent_searches_per_nda"] > 0 and m["config"]["agentic"] is True
    row = json.loads((Path(m["out_dir"]) / "reviews.jsonl").read_text().splitlines()[0])
    assert any(c["agent"] for c in row["checks"])


def test_compare_command(tmp_path, capsys):
    nda = tmp_path / "nda.txt"
    nda.write_text("The Recipient shall keep Confidential Information secret.\n", encoding="utf-8")
    main(["--config", str(ROOT / "configs" / "backends.toml"), "compare", "--backend", "fake", "--no-cache",
          "--pack", str(TOY_PACK), "--text", str(nda)])
    out = capsys.readouterr().out
    assert "agent_searches" in out and "agentic" in out
