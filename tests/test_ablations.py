"""Ablation report (docs/design/ablation-studies.md): pairing with the full system, the two-sided
bootstrap p-value and Holm's correction."""

from __future__ import annotations

import json

from counselcopilot.experiments.ablations import ablation_report, holm, label, paired_test, report_markdown


def metrics(name, per_doc, ablation=None, preset=None):
    tp, fp, fn = (sum(x[i] for x in per_doc) for i in range(3))
    prf = {"precision": tp / (tp + fp) if tp + fp else 0, "recall": tp / (tp + fn) if tp + fn else 0}
    prf["f1"] = round(2 * prf["precision"] * prf["recall"] / ((prf["precision"] + prf["recall"]) or 1), 4)
    return {"system": {"name": name, "ablation": ablation, "preset": preset}, "config": {},
            "strict": {"overall": prf, "by_type": {"omission": {"recall": prf["recall"]}}, "per_doc": per_doc,
                       "false_alarms_per_nda": 1.0},
            "checks_per_nda": 10, "usage": {"input_tokens_uncached": 100 * len(per_doc)}}


def write(tmp_path, name, m):
    d = tmp_path / name
    d.mkdir()
    (d / "metrics.json").write_text(json.dumps(m))
    return str(d)


def test_labels_separate_pipeline_ablations_reviewer_presets_and_baselines():
    assert label(metrics("pipeline", [], ablation="no_xref")) == "no_xref"
    assert label(metrics("reviewer", [], preset="full")) == "reviewer:full"
    assert label(metrics("b1", [])) == "b1"


def test_identical_systems_get_p_one_and_a_clear_drop_is_significant():
    same = [(3, 1, 1)] * 10
    assert paired_test(same, same)["p"] == 1.0
    worse = [(1, 1, 3)] * 10
    t = paired_test(worse, same, "recall")
    assert t["diff"] < 0 and t["p"] < 0.01 and t["ci95"][1] < 0


def test_holm_is_monotone_and_never_below_raw():
    adj = holm({"a": 0.01, "b": 0.04, "c": 0.03})
    assert adj == {"a": 0.03, "c": 0.06, "b": 0.06}


def test_report_pairs_every_run_with_full_and_corrects_only_the_ablations(tmp_path):
    full = [(3, 1, 1)] * 8
    runs = [write(tmp_path, "full", metrics("pipeline", full, ablation="full")),
            write(tmp_path, "nr", metrics("pipeline", [(1, 0, 3)] * 8, ablation="no_reverse")),
            write(tmp_path, "b2", metrics("b2", [(0, 2, 4)] * 8)),
            write(tmp_path, "short", metrics("pipeline", full[:3], ablation="no_xref")),
            "tuned_checker=" + write(tmp_path, "tuned", metrics("pipeline", full, ablation="full"))]
    rep = ablation_report(runs, n_boot=500)
    rows = rep["rows"]
    assert rows["no_reverse"]["d_recall"] < 0 and "p_holm_f1" in rows["no_reverse"]
    assert "p_f1" in rows["b2"] and "p_holm_f1" not in rows["b2"]
    assert rows["tuned_checker"]["d_f1"] == 0.0
    assert rep["skipped"] == {"no_xref": "different NDAs from the base run"}
    md = report_markdown(rep)
    assert "| no_reverse |" in md and "(raw)" in md and "omission recall down" in md
