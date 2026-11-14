"""Local-first cascade, simulated offline (proposal §7 ablation; design §8.2, cost-plan.md).

Both the local model (Llama / the QLoRA model) and Gemini answer every rule check in two RQ1 runs
of the same preset on the same NDAs and deals. For each confidence threshold the cascade keeps
the local answer when the local model is confident (and, optionally, the rule is not high
severity, and a second local model agrees), and takes Gemini's answer otherwise. Findings are
rebuilt from the chosen answers with the same label-to-finding mapping the reviewer uses and
scored against the same gold, so the cost-quality curve costs no extra API calls.

Reported per threshold: F1 and omission recall, share of checks escalated, estimated $ per NDA,
missed gold defects by severity; plus local-vs-remote agreement and the calibration (ECE) of the
local confidence against agreement with the remote answer.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from ..benchmark.align import Alignment, align, remap_findings
from ..benchmark.gold import GoldDefect, GoldNDA
from ..eval.metrics import score_detection
from ..policy.schema import DealContext, LawPack, PolicyPack, Rule
from ..review.checker import CheckResult, finding_from_check
from ..review.findings import FindingType


def _rows(path: str | Path) -> dict[int, dict]:
    p = Path(path)
    if p.is_dir():
        p = p / "reviews.jsonl"
    return {r["doc_id"]: r for r in (json.loads(l) for l in p.read_text().splitlines() if l.strip())}


def _gold(row: dict) -> GoldNDA:
    defects = [GoldDefect(g["rule_id"], FindingType(g["type"]), tuple(g["evidence"]), g["origin"]) for g in row["gold"]]
    return GoldNDA(row["doc_id"], DealContext.model_validate(row["deal"]), defects,
                   unscored_rules=row.get("unscored_rules", []))


def ece(conf: list[float], correct: list[bool], bins: int = 10) -> float:
    if not conf:
        return 0.0
    c, y = np.asarray(conf), np.asarray(correct, dtype=float)
    edges = np.linspace(0, 1, bins + 1)
    total = 0.0
    for lo, hi in zip(edges[:-1], edges[1:]):
        m = (c >= lo) & ((c < hi) if hi < 1 else (c <= hi))
        if m.any():
            total += m.mean() * abs(c[m].mean() - y[m].mean())
    return round(float(total), 4)


def simulate_cascade(local_run: str | Path, remote_run: str | Path, packs: list[PolicyPack],
                     law_pack: LawPack | None = None, gold_packs: list[PolicyPack] | None = None,
                     thresholds=(0.0, 0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 1.01), escalate_high_severity: bool = False,
                     second_local_run: str | Path | None = None, remote_cost_per_check: float | None = None) -> dict:
    local, remote = _rows(local_run), _rows(remote_run)
    second = _rows(second_local_run) if second_local_run else {}
    ids = sorted(set(local) & set(remote))
    rules: dict[str, dict[str, Rule]] = {p.company: {r.id: r for r in p.rules} for p in packs}
    law = {r.id: r for r in (law_pack.as_rules() if law_pack else [])}
    aligns: dict[str, Alignment] = ({p.company: align(p, g) for p, g in zip(packs, gold_packs)} if gold_packs else {})
    golds = {i: _gold(local[i]) for i in ids}

    # agreement and calibration of local confidence
    conf, agree = [], []
    for i in ids:
        rm = {(c["rule_id"], c["direction"]): c for c in remote[i]["checks"]}
        for c in local[i]["checks"]:
            o = rm.get((c["rule_id"], c["direction"]))
            if o is not None and not c["error"] and not o["error"]:
                conf.append(float(c["confidence"]))
                agree.append(c["label"] == o["label"])
    n_checks = sum(len(local[i]["checks"]) for i in ids)
    curve = []
    for t in thresholds:
        preds, escalated = {}, 0
        for i in ids:
            company = local[i]["deal"]["company"]
            rm = {(c["rule_id"], c["direction"]): c for c in remote[i]["checks"]}
            sm = {(c["rule_id"], c["direction"]): c for c in second.get(i, {}).get("checks", [])}
            fs = []
            for c in local[i]["checks"]:
                rule = rules.get(company, {}).get(c["rule_id"]) or law.get(c["rule_id"])
                if rule is None:
                    continue
                k = (c["rule_id"], c["direction"])
                use_remote = (c["confidence"] < t or c["error"]
                              or (escalate_high_severity and rule.severity.value == "high")
                              or (k in sm and sm[k]["label"] != c["label"]))
                src = rm.get(k) if use_remote and k in rm else c
                escalated += src is not c
                res = CheckResult(src["label"], src["evidence"], src["confidence"], "", src["shown"], src["error"])
                if c["direction"] == "field":
                    # field findings were judged on extracted values; keep the chosen run's finding
                    run = remote if src is not c else local
                    fs += [f for f in _findings_of(run[i], c["rule_id"])]
                    continue
                f = finding_from_check(rule, res, str(i), direction=c["direction"])
                if f is not None:
                    fs.append(f)
            preds[i] = remap_findings(fs, aligns[company]) if company in aligns else fs
        m = score_detection(preds, golds, ci=False)
        missed = {"high": 0, "medium": 0, "low": 0}
        for i in ids:
            got = {(f.rule_id, f.type.value) for f in preds[i]}
            for d in golds[i].defects:
                if d.key not in got:
                    r = rules.get(local[i]["deal"]["company"], {}).get(d.rule_id) or law.get(d.rule_id)
                    missed[r.severity.value if r else "medium"] += 1
        row = {"threshold": t, "f1": m["overall"]["f1"], "recall": m["overall"]["recall"],
               "omission_recall": m["by_type"].get("omission", {}).get("recall"),
               "escalated_share": round(escalated / n_checks, 4) if n_checks else 0.0,
               "missed_by_severity": missed}
        if remote_cost_per_check is not None:
            row["remote_usd_per_nda"] = round(escalated * remote_cost_per_check / max(len(ids), 1), 5)
        curve.append(row)
    return {"n_ndas": len(ids), "n_checks": n_checks,
            "agreement": round(float(np.mean(agree)), 4) if agree else None,
            "local_confidence_ece": ece(conf, agree), "curve": curve}


def _findings_of(row: dict, rule_id: str):
    from ..review.findings import Finding

    for f in row.get("findings", []):
        if f["rule_id"] == rule_id and f.get("direction") == "field":
            yield Finding.model_validate(f)


def pick_threshold(curve: list[dict], max_f1_drop: float = 0.01) -> dict:
    """Choose on dev: the lowest escalation share whose F1 is within `max_f1_drop` of all-remote."""
    best = max(c["f1"] for c in curve)
    ok = [c for c in curve if c["f1"] >= best - max_f1_drop]
    return min(ok, key=lambda c: c["escalated_share"])
