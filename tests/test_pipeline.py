from counselcopilot.benchmark.gold import gold_for
from counselcopilot.data.contractnli import load_contractnli
from counselcopilot.data.draft import Draft, Edit
from counselcopilot.eval.metrics import score_detection
from counselcopilot.experiments.nli import run_nli
from counselcopilot.experiments.rq1 import run_rq1
from counselcopilot.llm import FakeClient
from counselcopilot.policy.schema import DealContext, PolicyPack
from counselcopilot.retrieval.index import HybridIndex, Passage
from counselcopilot.review.findings import FindingType
from counselcopilot.review.policy_reviewer import PolicyReviewer, ReviewConfig

from .conftest import TOY_PACK, oracle_responder


def test_bm25_finds_return_clause(cnli_dir):
    doc = load_contractnli(cnli_dir).by_id(1)
    idx = HybridIndex([Passage(str(i), s) for i, s in enumerate(doc.span_texts)])
    assert idx.search("return or destroy information on termination", k=1)[0].passage.id == "3"


def test_draft_edits():
    d = Draft("x", ["a", "b", "c"])
    e = d.apply([Edit("replace", 1, "B"), Edit("insert_after", 2, "d"), Edit("delete", 0)])
    assert e.segments == ["B", "c", "d"] and e.source_ids == [None, 2, None]


def _review(cnli_dir, doc_id, preset, **deal_kw):
    pack = PolicyPack.load(TOY_PACK)
    doc = load_contractnli(cnli_dir).by_id(doc_id)
    deal = DealContext(company="ToyCo", **deal_kw)
    res = PolicyReviewer(FakeClient(oracle_responder), pack, ReviewConfig.preset(preset)).review(
        Draft.from_nda(doc), deal)
    return {(f.rule_id, f.type) for f in res.findings}, res


def test_reverse_finds_omissions(cnli_dir):
    found, _ = _review(cnli_dir, 2, "full", counterparty_type="vendor")
    assert ("P-01", FindingType.OMISSION) in found  # no return clause
    assert ("P-02", FindingType.OMISSION) in found  # oral not covered
    assert ("P-03", FindingType.OMISSION) in found  # no survival
    assert ("P-12", FindingType.APPROVAL_NEEDED) in found  # Singapore law needs GC sign-off
    assert ("P-07", FindingType.VIOLATION) not in found  # non-solicit only forbidden for customers


def test_forward_only_cannot_find_omissions(cnli_dir):
    found, _ = _review(cnli_dir, 2, "no_reverse", counterparty_type="customer")
    assert not any(t == FindingType.OMISSION and r != "P-11" and r != "P-12" for r, t in found)
    assert ("P-07", FindingType.VIOLATION) in found  # forward still catches the non-solicit


def test_clean_doc_has_no_return_finding(cnli_dir):
    found, _ = _review(cnli_dir, 1, "full", counterparty_type="vendor")
    assert ("P-01", FindingType.OMISSION) not in found
    assert ("P-12", FindingType.APPROVAL_NEEDED) not in found


def test_no_filter_raises_false_alarms(cnli_dir):
    data = load_contractnli(cnli_dir)
    pack = PolicyPack.load(TOY_PACK)
    deal = DealContext(company="ToyCo", counterparty_type="vendor")
    gold = {2: gold_for(data.by_id(2), deal, pack)}
    scores = {}
    for preset in ("full", "no_filter"):
        res = PolicyReviewer(FakeClient(oracle_responder), pack, ReviewConfig.preset(preset)).review(
            Draft.from_nda(data.by_id(2)), deal)
        scores[preset] = score_detection({2: res.findings}, gold)
    assert scores["no_filter"]["false_alarms_per_nda"] > scores["full"]["false_alarms_per_nda"]
    assert scores["full"]["overall"]["recall"] == 1.0


def test_runners_write_outputs(cnli_dir, tmp_path):
    data = load_contractnli(cnli_dir)
    m = run_nli(FakeClient(oracle_responder), data, "dev", "nda-3,nda-16", out_root=str(tmp_path))
    assert m["all"]["n"] == 4 and m["all"]["accuracy"] == 1.0
    m = run_rq1(FakeClient(oracle_responder), data, [PolicyPack.load(TOY_PACK)], "dev",
                out_root=str(tmp_path))
    assert m["strict"]["n_ndas"] == 2
