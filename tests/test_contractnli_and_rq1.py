"""ContractNLI handling (proposal §5, §6: 17 checks, 12 trained and 5 held out; three natural
loophole checks, standard carve-outs not counted) and an end-to-end RQ1 run on a fake dataset
(proposal §7: strict, lenient and rule-only scores, natural vs planted, false alarms, check counts,
deal-fact accuracy and the change in recall on NDAs with prompt-injection text)."""

import json
import random

import pytest

from conftest import ALL_HYPOTHESES, COMPLIANT_SEGMENTS, KeywordLLM, deal, make_doc, make_law_pack, make_pack
from counselcopilot.benchmark.planter import Planter
from counselcopilot.data.contractnli import (HELD_OUT_HYPOTHESES, LOOPHOLE_LABELS, STANDARD_CARVE_OUTS, ContractNLI,
                                             Hypothesis, load_contractnli)
from counselcopilot.experiments.nli import resolve_hypotheses, run_nli
from counselcopilot.experiments.rq1 import run_rq1


RETURN_HYP = "Receiving Party shall destroy or return some Confidential Information upon the termination of Agreement."


def hyp_text(h: str) -> str:
    return RETURN_HYP if h == "nda-16" else f"Hypothesis {h}."


def write_split(root, split, docs):
    raw = {"labels": {h: {"short_description": h, "hypothesis": hyp_text(h)} for h in ALL_HYPOTHESES},
           "documents": [{"id": d.id, "file_name": d.file_name, "text": d.text, "spans": [list(s) for s in d.spans],
                          "annotation_sets": [{"annotations": {h: {"choice": a.label.value, "spans": list(a.spans)}
                                                               for h, a in d.annotations.items()}}],
                          "document_type": "search-pdf", "url": ""} for d in docs]}
    (root / f"{split}.json").write_text(json.dumps(raw))


NLI = {"nda-16": ("Entailment", (2,)), "nda-3": ("Entailment", (1,))}


@pytest.fixture
def data(tmp_path):
    root = tmp_path / "contract-nli"
    root.mkdir()
    for split, ids in (("train", [1]), ("dev", [2, 3]), ("test", [4, 5, 6, 7])):
        write_split(root, split, [make_doc(doc_id=i, labels=NLI, split=split) for i in ids])
    return load_contractnli(tmp_path)


# ------------------------------------------------------------------ the loader

def test_loader_reads_splits_spans_and_labels(data):
    assert [len(data[s]) for s in ("train", "dev", "test")] == [1, 2, 4]
    d = data.by_id(4)
    assert d.split == "test" and d.span_texts == COMPLIANT_SEGMENTS
    assert d.annotations["nda-16"].label.value == "Entailment" and d.evidence_text("nda-16") == [COMPLIANT_SEGMENTS[2]]
    with pytest.raises(KeyError):
        data.by_id(99)


def test_missing_split_says_how_to_download(tmp_path):
    with pytest.raises(FileNotFoundError, match="cc data download"):
        load_contractnli(tmp_path)


def test_hypotheses_sort_numerically_and_five_are_held_out(data):
    keys = data.hypothesis_keys
    assert len(keys) == 17 and keys[:3] == ["nda-1", "nda-2", "nda-3"] and keys[-1] == "nda-20"
    assert len(HELD_OUT_HYPOTHESES) == 5 and len(data.train_hypotheses()) == 12
    assert not set(HELD_OUT_HYPOTHESES) & set(data.train_hypotheses())
    assert Hypothesis("nda-16", "", "").held_out


def test_label_counts(data):
    c = data.label_counts("test")
    assert c["nda-16"] == {"Entailment": 4, "Contradiction": 0, "NotMentioned": 0}


def test_natural_loopholes_are_the_three_proposal_checks():
    """Technical-only definition (nda-2), oral disclosures excluded (nda-3 contradicted),
    retained copies (nda-20); independent development and third-party acquisition are not."""
    assert LOOPHOLE_LABELS == {"nda-2": "Entailment", "nda-3": "Contradiction", "nda-20": "Entailment"}
    assert set(STANDARD_CARVE_OUTS) == {"nda-12", "nda-13"} and not set(STANDARD_CARVE_OUTS) & set(LOOPHOLE_LABELS)


def test_resolve_hypotheses(data):
    assert resolve_hypotheses(data, "held_out") == list(HELD_OUT_HYPOTHESES)
    assert resolve_hypotheses(data, "train") == data.train_hypotheses()
    assert resolve_hypotheses(data, "nda-3, nda-16") == ["nda-3", "nda-16"]


def test_nli_run_scores_the_prompted_checker(data, tmp_path):
    llm = KeywordLLM(keywords={RETURN_HYP: ("destroy", None)})
    m = run_nli(llm, data, "dev", "nda-16,nda-3", k=12, max_workers=1, out_root=str(tmp_path / "runs"))
    assert m["nda-16"]["accuracy"] == 1.0 and m["nda-3"]["accuracy"] == 0.0  # nda-3: nothing retrieved
    assert m["all"]["retrieval_evidence_recall"] == 0.5 and m["errors"] == 0  # nda-3 evidence never retrieved
    assert (tmp_path / "runs").exists()


# ------------------------------------------------------------------ RQ1 end to end

FIELDS = {"confidentiality_term_months": "four (4) years", "governing_law": "Delaware"}
HINTS = {"confidentiality_term_months": "years", "governing_law": "governed"}


def labels_file(tmp_path, ids):
    import yaml

    path = tmp_path / "labels.yaml"
    path.write_text(yaml.safe_dump({i: {"verified": True, "governing_law": "delaware", "personal_data": False,
                                        "fields": {"confidentiality_term_months": 48}} for i in ids}))
    return str(path)


def test_rq1_full_system_on_clean_ndas_has_no_false_alarms(data, tmp_path):
    m = run_rq1(KeywordLLM(fields=FIELDS, field_hints=HINTS), data, [make_pack()], split="test",
                labels_path=labels_file(tmp_path, [4, 5, 6, 7]), deals={i: deal() for i in (4, 5, 6, 7)},
                out_root=str(tmp_path / "runs"), max_workers=1, law_pack=make_law_pack())
    assert m["strict"]["overall"]["fp"] == 0 and m["strict"]["false_alarms_per_nda"] == 0.0
    assert m["check_errors"] == 0 and m["checks_per_nda"] > 0
    assert set(m) >= {"strict", "lenient", "rule_only", "fact_accuracy", "usage", "config"}
    out = m["out_dir"]
    rows = [json.loads(line) for line in open(f"{out}/reviews.jsonl")]
    assert len(rows) == 4 and all("checks" in r and "gold" in r for r in rows)


def test_rq1_with_hidden_facts_scores_fact_accuracy(data, tmp_path):
    m = run_rq1(KeywordLLM(fields=FIELDS, field_hints=HINTS, personal_data=False), data, [make_pack()],
                split="test", labels_path=labels_file(tmp_path, [4, 5, 6, 7]), hide_facts=True,
                deals={i: deal() for i in (4, 5, 6, 7)}, out_root=str(tmp_path / "runs"), max_workers=1)
    assert m["fact_accuracy"]["governing_law"] == {"accuracy": 1.0, "n": 4}
    assert m["fact_accuracy"]["personal_data"] == {"accuracy": 1.0, "n": 4}
    assert m["config"]["hide_facts"] is True


def test_rq1_on_planted_ndas_finds_planted_omissions_and_reports_injection(data, tmp_path):
    pack, law = make_pack(), make_law_pack()
    planter = Planter(pack, law)
    labels = {"governing_law": "delaware", "personal_data": False, "fields": {"confidentiality_term_months": 48}}
    planted = {}
    for doc in data["test"]:
        rng = random.Random(doc.id)
        planted[doc.id] = planter.plant(doc, deal(governing_law=None), rng, n_defects=2, labels=labels,
                                        injection=doc.id % 2 == 0)
    m = run_rq1(KeywordLLM(fields=FIELDS, field_hints=HINTS), data, [pack], split="test", planted=planted,
                labels_path=labels_file(tmp_path, [4, 5, 6, 7]), out_root=str(tmp_path / "runs"),
                max_workers=1, law_pack=law)
    assert m["planted_only"]["n_gold_defects"] > 0
    omissions = m["strict"]["by_type"].get("omission", {})
    assert omissions.get("fn", 0) == 0  # the fake checker never misses a deleted clause
    assert m["injection"]["injected"]["n_ndas"] == 2 and m["injection"]["clean"]["n_ndas"] == 2


def test_rq1_forward_only_reports_no_omissions(data, tmp_path):
    m = run_rq1(KeywordLLM(fields=FIELDS, field_hints=HINTS), data, [make_pack()], split="test", preset="no_reverse",
                labels_path=labels_file(tmp_path, [4, 5, 6, 7]), deals={i: deal() for i in (4, 5, 6, 7)},
                out_root=str(tmp_path / "runs"), max_workers=1)
    assert m["strict"]["by_type"].get("omission", {}).get("tp", 0) == 0
