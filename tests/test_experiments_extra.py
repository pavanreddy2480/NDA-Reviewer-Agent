"""Proposal §5-§7 support pieces: RQ2 scoring and blind acceptance, the cost cascade, the policy-size
sweep, fine-tuning data, the synthetic mini-benchmark, the offline heuristic backend and the smoke run."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from counselcopilot.benchmark.synthetic import synthetic_contractnli, write_synthetic
from counselcopilot.data.contractnli import HELD_OUT_HYPOTHESES, load_contractnli
from counselcopilot.experiments.cascade import ece, pick_threshold
from counselcopilot.experiments.rq2 import acceptance_kappa, acceptance_sheet, aggregate, paired_remaining
from counselcopilot.experiments.sweep import approx_tokens, pad_policies
from counselcopilot.finetune.data import build_all, cuad_tag_f1, frame_examples, nli_examples

ROOT = Path(__file__).resolve().parents[1]


# ------------------------------------------------------------------ synthetic data

def test_synthetic_set_has_the_proposal_splits_and_labels_for_every_nda():
    data, labels = synthetic_contractnli(seed=0)
    assert {s: len(data[s]) for s in ("train", "dev", "test")} == {"train": 8, "dev": 6, "test": 12}
    assert set(labels) == {d.id for s in ("train", "dev", "test") for d in data[s]}
    again, _ = synthetic_contractnli(seed=0)
    assert [d.text for d in again["test"]] == [d.text for d in data["test"]]  # deterministic


def test_synthetic_set_round_trips_through_the_contractnli_loader(tmp_path):
    info = write_synthetic(tmp_path / "s", seed=1)
    data = load_contractnli(info["root"])
    assert len(data["test"]) == info["n"]["test"]
    doc = data["test"][0]
    for a in doc.annotations.values():  # every evidence span points into the document
        assert all(0 <= i < len(doc.spans) for i in a.spans)


# ------------------------------------------------------------------ fine-tuning data

def test_nli_training_examples_never_contain_the_held_out_hypotheses():
    data, _ = synthetic_contractnli(seed=0)
    ex = nli_examples(data, "train", limit=2)
    held = {data.hypotheses[h].text for h in HELD_OUT_HYPOTHESES if h in data.hypotheses}
    assert ex and all(not any(t in e["messages"][1]["content"] for t in held) for e in ex)
    ans = json.loads(ex[0]["messages"][2]["content"])
    assert set(ans) >= {"label", "evidence", "confidence"}


def test_cuad_tag_f1_micro_and_macro():
    m = cuad_tag_f1([["A", "B"], ["A"]], [["A"], ["A", "C"]])
    assert m["micro_f1"] == round(2 * 2 / (2 * 2 + 1 + 1), 4) and m["n_types"] == 3


def test_frame_examples_drop_the_source_field_and_build_all_splits(tmp_path):
    silver = tmp_path / "silver.jsonl"
    silver.write_text(json.dumps({"doc_id": 1, "segments": ["A.", "The term is two years."], "ids": [1],
                                  "frames": [{"segment": 1, "clause_type": "term", "duration": "two years",
                                              "source": "regex"}]}) + "\n")
    fx = frame_examples(silver)
    assert len(fx) == 1 and "source" not in fx[0]["messages"][2]["content"]
    nli = [{"task": "nli", "messages": []} for _ in range(40)]
    man = build_all(tmp_path / "ft", nli, frames=fx)
    assert man["train"] + man["val"] == 41 and man["val"] == 2
    assert (tmp_path / "ft" / "train.jsonl").exists() and man["held_out_hypotheses"] == list(HELD_OUT_HYPOTHESES)


# ------------------------------------------------------------------ cascade

def test_ece_is_zero_when_confidence_matches_accuracy():
    assert ece([1.0, 1.0, 0.0], [True, True, False]) == 0.0
    assert ece([0.9, 0.9], [False, False]) == 0.9
    assert ece([], []) == 0.0


def test_pick_threshold_takes_the_cheapest_point_within_the_f1_drop():
    curve = [{"t": 0.0, "f1": 0.80, "escalated_share": 1.0}, {"t": 0.7, "f1": 0.795, "escalated_share": 0.3},
             {"t": 0.9, "f1": 0.70, "escalated_share": 0.1}]
    assert pick_threshold(curve)["t"] == 0.7


# ------------------------------------------------------------------ sweep

def test_pad_policies_reaches_the_target_and_renames_the_company(tmp_path):
    src = ROOT / "packs/policynda/saas/policies"
    pads = [ROOT / "packs/policynda/hospital/policies"]
    base = sum(approx_tokens(p.read_text()) for p in src.glob("*.md"))
    info = pad_policies(src, tmp_path / "padded", base + 2000, pads, company_name="SaaSCo")
    assert info["tokens"] >= base + 2000 and info["padding_docs"]
    text = (tmp_path / "padded" / info["padding_docs"][0]).read_text()
    assert "**Company:**" not in text or "**Company:** SaaSCo" in text


# ------------------------------------------------------------------ rq2 scoring

def row(system, doc, remaining, **kw):
    base = dict(system=system, doc_id=doc, remaining_problems=remaining, redlines=2, regressed_redlines=0,
                gold_repairs=[{"success": True, "restores_original": False}], attacker=None, loopholes_left=[],
                edit_words=10, rounds=1, tokens=100, stopped="clean", escalations=[])
    return {**base, **kw}


def test_aggregate_and_paired_ratio_for_h2():
    rows = [row("loop", i, 1) for i in range(5)] + [row("r1", i, 4, regressed_redlines=1) for i in range(5)]
    agg = aggregate(rows)
    assert agg["loop"]["remaining_per_nda"] == 1.0 and agg["r1"]["regression_rate"] == 0.5
    assert agg["loop"]["repair_success"] == 1.0 and agg["loop"]["stopped"] == {"clean": 5}
    pr = paired_remaining(rows, "loop", "r1")
    assert pr["ratio"] == 0.25 and pr["h2_half"] is True
    assert paired_remaining(rows, "loop", "nobody") is None


def test_blind_acceptance_sheet_hides_systems_and_kappa_reads_it_back(tmp_path):
    rep = tmp_path / "repairs.jsonl"
    edits = [{"op": "replace", "before": "old clause", "text": "new clause"}]
    rep.write_text("\n".join(json.dumps({"system": s, "doc_id": d, "edits": edits})
                             for s in ("loop", "r1") for d in (1, 2)) + "\n")
    sheet = acceptance_sheet(rep, tmp_path / "sheet.csv", n_ndas=2)
    rows = list(csv.DictReader(sheet.open()))
    assert len(rows) == 4 and "system" not in rows[0]
    key = json.loads(sheet.with_suffix(".key.json").read_text())
    for name in ("a", "b"):  # both raters accept every loop redline and reject every r1 redline
        with (tmp_path / f"{name}.csv").open("w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0]))
            w.writeheader()
            for r in rows:
                w.writerow({**r, "accept (y/n)": "y" if key[r["item"]] == "loop" else "n"})
    k = acceptance_kappa(tmp_path / "a.csv", tmp_path / "b.csv", sheet.with_suffix(".key.json"))
    assert k["kappa"] == 1.0 and k["per_system"]["loop"]["accept_rate"] == 1.0 and k["h2_loop_accept_70pct"]


# ------------------------------------------------------------------ heuristic backend and smoke run

def test_heuristic_backend_answers_an_nli_check():
    from counselcopilot.llm.base import system, user
    from counselcopilot.llm.heuristic import HeuristicClient
    from counselcopilot.review.checker import CHECK_SYSTEM

    out = HeuristicClient().complete([system(CHECK_SYSTEM), user(
        "STATEMENT: The Receiving Party shall return or destroy confidential information.\n\nSEGMENTS:\n"
        "[0] The Receiving Party shall return or destroy all Confidential Information on request.")], tag="check")
    ans = json.loads(out.text)
    assert ans["label"] in ("Entailment", "Contradiction", "NotMentioned")


def test_smoke_run_executes_every_experiment_offline(tmp_path, monkeypatch):
    from counselcopilot.commands import run_smoke

    monkeypatch.chdir(ROOT)
    s = run_smoke(str(tmp_path / "smoke"))
    table = Path(s["table"]).read_text()
    for name in ("reviewer:full", "pipeline:full", "b1", "b3", "loop", "r2"):
        assert name in table
    assert len(s["runs"]) == 13 and "accuracy" in s["nli"]
