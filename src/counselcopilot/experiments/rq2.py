"""RQ2 runner: the red-team and repair loop against R1, R1+A, R2 and the loop ablations.

For each planted benchmark NDA:
1. the full detection pipeline finds problems (the same findings go to every repair system);
2. each repair system edits the draft under the same token budget;
3. the *independent* evaluator (a backend never used inside any loop, eval/evaluator.py) scores
   the edited draft: rules fixed, remaining, and regressions (each confirmed by a second run);
   gold repairs for planted defects (the original clause), loopholes left (planted clauses still
   in the draft; natural ContractNLI loopholes re-checked with their hypothesis), and regressions
   attributed to single redlines for H2's per-redline rate.

H2 is checked directly: remaining problems per NDA at most half of R1's and R1+A's, fewer than 5%
of redlines introduce a new violation. Blind acceptance (>= 70%) needs people: `acceptance_sheet`
writes the sheet for two teammates and `acceptance_kappa` scores it.
"""

from __future__ import annotations

import csv
import json
import random
import re
from dataclasses import replace
from pathlib import Path

import numpy as np

from ..agents.pipeline import CounselCopilot, PipelineConfig
from ..benchmark.gold import gold_deal
from ..benchmark.labels import load_labels
from ..benchmark.planter import PlantedNDA
from ..data.contractnli import LOOPHOLE_LABELS
from ..data.draft import Draft
from ..eval.evaluator import IndependentEvaluator
from ..eval.metrics import bootstrap_ci, cohen_kappa
from ..llm import LLMClient, PendingBatch
from ..policy.schema import LawPack, PolicyPack, Rule
from ..repair.attacker import OpposingCounsel, loophole_scores
from ..repair.loop import RedTeamRepairLoop, RepairResult, one_shot, self_refine
from ..repair.repairer import Repairer, edit_size
from .common import run_dir, usage_report, write_jsonl

SYSTEMS = ("loop", "r1", "r1_attacker", "r2", "loop_no_attacker", "loop_no_regression", "loop_1_round")


def _words(s: str) -> set[str]:
    return set(re.findall(r"[a-z]{3,}", s.lower()))


def restores_original(final: Draft, originals: list[str], min_overlap: float = 0.6) -> bool:
    """A segment of the repaired draft carries the gold original clause's wording."""
    for o in originals:
        wo = _words(o)
        if wo and any(len(wo & _words(s)) / len(wo) >= min_overlap for s in final.segments):
            return True
    return False


def loopholes_left(ev: IndependentEvaluator, final: Draft, planted: PlantedNDA,
                   hypotheses: dict[str, str] | None) -> list[str]:
    left = []
    for lh in planted.loopholes:
        if lh.get("origin") == "planted":
            texts = [planted.draft.segments[i] for i in lh.get("evidence", []) if i < len(planted.draft.segments)]
            if texts and any(t in final.segments for t in texts):
                left.append(lh.get("topic", "planted"))
        elif hypotheses and lh.get("hypothesis") in hypotheses:
            h = lh["hypothesis"]
            rule = Rule(id="EVAL-LOOP", title=h, requirement=hypotheses[h], term=hypotheses[h], kind="require")
            if ev.check(rule, final).result.label == LOOPHOLE_LABELS[h]:
                left.append(h)
    return left


def make_system(name: str, repairer: Repairer, attacker: OpposingCounsel, detector, rules: list[Rule],
                max_rounds: int, budget: int | None, clients: list[LLMClient]):
    if name == "r1":
        return lambda d, deal, fs: one_shot(repairer, d, fs, rules, clients=clients)
    if name == "r1_attacker":
        return lambda d, deal, fs: one_shot(repairer, d, fs, rules, attacker, deal, clients=clients)
    if name == "r2":
        return lambda d, deal, fs: self_refine(repairer, d, fs, rules, max_rounds, budget, clients)
    loop_kw = dict(rules=rules, max_rounds=max_rounds, token_budget=budget, clients=clients, name=name)
    if name == "loop":
        lp = RedTeamRepairLoop(repairer, detector, attacker, **loop_kw)
    elif name == "loop_no_attacker":
        lp = RedTeamRepairLoop(repairer, detector, None, **loop_kw)
    elif name == "loop_no_regression":
        lp = RedTeamRepairLoop(repairer, None, attacker, **loop_kw)
    elif name == "loop_1_round":
        lp = RedTeamRepairLoop(repairer, detector, attacker, **{**loop_kw, "max_rounds": 1})
    else:
        raise KeyError(f"unknown RQ2 system {name!r}; choose from {SYSTEMS}")
    return lp.run


def score_one(ev: IndependentEvaluator, res: RepairResult, planted: PlantedNDA, rules: list[Rule], deal,
              hypotheses: dict[str, str] | None, attribute: bool = True) -> dict:
    s = ev.score_repair(planted.draft, res.final, rules, deal)
    fixed = set(s["fixed"])
    gold = []
    for rep in planted.gold_repairs:
        rid, kind = rep["rule_id"], rep["kind"]
        if kind == "delete":
            texts = [planted.draft.segments[i] for i in rep.get("position", []) if i < len(planted.draft.segments)]
            ok = bool(texts) and not any(t in res.final.segments for t in texts)
        else:
            ok = rid in fixed or restores_original(res.final, rep.get("original", []))
        gold.append({"rule_id": rid, "kind": kind, "success": ok,
                     "restores_original": restores_original(res.final, rep.get("original", [])) if kind != "delete" else ok})
    lh_left = loopholes_left(ev, res.final, planted, hypotheses)
    by_id = {r.id: r for r in rules}
    redlines = regressed_redlines = 0
    if attribute and s["regressions"]:
        for rnd in res.rounds:
            att = ev.attribute(rnd.base, rnd.edits, [by_id[i] for i in s["regressions"] if i in by_id], s["regressions"])
            redlines += len(rnd.edits)
            regressed_redlines += sum(bool(v) for v in att.values())
    else:
        redlines = len(res.edits)
    size = [edit_size(r.base, r.edits) for r in res.rounds]
    return {
        "doc_id": planted.doc_id, "system": res.system, **res.summary(),
        "fixed": s["fixed"], "remaining": s["remaining"], "regressions": s["regressions"],
        "loopholes_left": lh_left, "n_loopholes": len(planted.loopholes),
        "remaining_problems": len(s["remaining"]) + len(lh_left),
        "redlines": redlines, "regressed_redlines": regressed_redlines,
        "gold_repairs": gold, "edit_words": sum(x["words"] for x in size),
        "attacker": loophole_scores(res.scenarios, planted.loopholes) if res.scenarios else None,
        "escalations": res.escalations,
        "edits": [{"round": r.round, "op": e.op, "segment": e.segment, "text": e.text, "fixes": e.reason,
                   "before": r.base.segments[e.segment] if 0 <= e.segment < len(r.base.segments) else ""}
                  for r in res.rounds for e in r.edits],
    }


def aggregate(rows: list[dict]) -> dict:
    out = {}
    for sysname in sorted({r["system"] for r in rows}):
        rs = [r for r in rows if r["system"] == sysname]
        rem = [r["remaining_problems"] for r in rs]
        red = sum(r["redlines"] for r in rs)
        gold = [g for r in rs for g in r["gold_repairs"]]
        att = [r["attacker"] for r in rs if r["attacker"]]
        n_gold_lh = sum(a["n_gold"] for a in att)
        out[sysname] = {
            "n_ndas": len(rs),
            "remaining_per_nda": round(float(np.mean(rem)), 3) if rem else None,
            "remaining_ci95": [round(x, 3) for x in bootstrap_ci(rem)],
            "loopholes_left_per_nda": round(float(np.mean([len(r["loopholes_left"]) for r in rs])), 3),
            "regression_rate": round(sum(r["regressed_redlines"] for r in rs) / red, 4) if red else 0.0,
            "redlines": red,
            "repair_success": round(sum(g["success"] for g in gold) / len(gold), 4) if gold else None,
            "restores_original": round(sum(g["restores_original"] for g in gold) / len(gold), 4) if gold else None,
            "edit_words_per_nda": round(float(np.mean([r["edit_words"] for r in rs])), 1),
            "rounds_mean": round(float(np.mean([r["rounds"] for r in rs])), 2),
            "tokens_per_nda": round(float(np.mean([r["tokens"] for r in rs])), 1),
            "stopped": {k: sum(r["stopped"] == k for r in rs) for k in sorted({r["stopped"] for r in rs})},
            "escalations_per_nda": round(float(np.mean([len(r["escalations"]) for r in rs])), 3),
            "attacker_loophole_recall": (round(sum((a["recall"] or 0) * a["n_gold"] for a in att) / n_gold_lh, 4)
                                         if n_gold_lh else None),
            "attacker_precision": (round(float(np.mean([a["precision"] for a in att if a["precision"] is not None])), 4)
                                   if any(a["precision"] is not None for a in att) else None),
        }
    return out


def paired_remaining(rows: list[dict], a: str, b: str, n: int = 5000, seed: int = 0) -> dict | None:
    """Loop vs a baseline on the same NDAs: ratio of mean remaining problems (H2: <= 0.5) with a
    paired bootstrap 95% CI."""
    A = {r["doc_id"]: r["remaining_problems"] for r in rows if r["system"] == a}
    B = {r["doc_id"]: r["remaining_problems"] for r in rows if r["system"] == b}
    ids = sorted(set(A) & set(B))
    if not ids:
        return None
    x, y = np.array([A[i] for i in ids], float), np.array([B[i] for i in ids], float)
    idx = np.random.default_rng(seed).integers(0, len(ids), size=(n, len(ids)))
    with np.errstate(divide="ignore", invalid="ignore"):
        ratios = x[idx].mean(1) / np.where(y[idx].mean(1) == 0, np.nan, y[idx].mean(1))
    ratios = ratios[~np.isnan(ratios)]
    point = float(x.mean() / y.mean()) if y.mean() else None
    return {"a": a, "b": b, "n": len(ids), "ratio": round(point, 4) if point is not None else None,
            "ratio_ci95": [round(float(np.quantile(ratios, 0.025)), 4), round(float(np.quantile(ratios, 0.975)), 4)]
            if len(ratios) else None,
            "h2_half": bool(point is not None and point <= 0.5)}


def run_rq2(llm: LLMClient, packs: list[PolicyPack], planted: dict[int, PlantedNDA], evaluator_llm: LLMClient,
            law_pack: LawPack | None = None, systems: tuple[str, ...] = ("loop", "r1", "r1_attacker", "r2"),
            checker_llm: LLMClient | None = None, attacker_llm: LLMClient | None = None,
            gold_packs: list[PolicyPack] | None = None, labels_path: str | None = None,
            allow_auto_labels: bool = False, hypotheses: dict[str, str] | None = None, limit: int | None = None,
            max_rounds: int = 3, token_budget: int | None = None, out_root: str = "runs",
            detection: PipelineConfig | None = None, noise_floor: int = 0, seed: int = 0) -> dict:
    if evaluator_llm is llm or evaluator_llm is checker_llm or (attacker_llm is not None and evaluator_llm is attacker_llm):
        raise ValueError("the RQ2 evaluator must be a backend no repair system uses (eval/evaluator.py)")
    by_company = {p.company: p for p in packs}
    gold_by_company = {p.company: p for p in (gold_packs or packs)}
    labels = load_labels(labels_path, allow_auto=allow_auto_labels) if labels_path else {}
    law_rules = law_pack.as_rules() if law_pack else []
    ev = IndependentEvaluator(evaluator_llm)
    clients = [c for c in (llm, checker_llm, attacker_llm) if c is not None]
    det_cfg = detection or PipelineConfig()
    regress_cfg = replace(PipelineConfig(), verifier=False, tool_agent=False, planner="fixed", review=det_cfg.review)
    docs = sorted(planted)[:limit] if limit else sorted(planted)
    rows, detections, drafts_out, pending = [], [], [], 0
    for doc_id in docs:
        p = planted[doc_id]
        pack = by_company[p.deal.company]
        detector_pipe = CounselCopilot(llm, pack, law_pack, det_cfg, checker_llm)
        regress_pipe = CounselCopilot(llm, pack, law_pack, regress_cfg, checker_llm)
        try:
            det = detector_pipe.review(p.draft, p.deal)
        except PendingBatch:
            pending += 1
            continue
        resolved = {e.rule_id for e in (det.handoff.resolved if det.handoff else [])}
        findings = [f for f in det.findings + det.unscored_findings if f.rule_id not in resolved]
        detections.append({"doc_id": doc_id, "findings": [f.model_dump(mode="json") for f in findings]})
        rules = list(pack.rules) + law_rules
        repairer = Repairer(llm)
        deal = gold_deal(p.deal, {**labels.get(doc_id, {}), **p.label_updates})
        eval_rules = list(gold_by_company[p.deal.company].rules) + law_rules
        for name in systems:
            # a fresh attacker per system: its scenario ids (S-001, ...) go into the repair prompts, so a shared
            # counter would make one system's redlines depend on which systems ran before it
            attacker = OpposingCounsel(attacker_llm or llm)
            run = make_system(name, repairer, attacker, regress_pipe.detect, rules, max_rounds, token_budget, clients)
            try:
                res = run(p.draft, p.deal, findings)
            except PendingBatch:
                pending += 1
                continue
            res.system = name
            # saved before scoring, so the repaired NDA is on disk even while the judge's answers are pending
            drafts_out.append({"doc_id": doc_id, "system": name, "company": p.deal.company,
                               "stopped": res.stopped, "rounds": len(res.rounds),
                               "edits": [{"round": r.round, "op": e.op, "segment": e.segment, "text": e.text,
                                          "fixes": e.reason} for r in res.rounds for e in r.edits],
                               "original": list(p.draft.segments), "repaired": list(res.final.segments),
                               "repaired_text": "\n".join(res.final.segments)})
            try:
                rows.append(score_one(ev, res, p, eval_rules, deal, hypotheses))
            except PendingBatch:
                pending += 1
    agg = aggregate(rows)
    comparisons = [c for c in (paired_remaining(rows, "loop", b) for b in systems if b != "loop") if c]
    reg = agg.get("loop", {}).get("regression_rate")
    metrics = {
        "systems": agg, "comparisons": comparisons,
        "h2": {"remaining_at_most_half_of_r1": next((c["h2_half"] for c in comparisons if c["b"] == "r1"), None),
               "remaining_at_most_half_of_r1_attacker": next((c["h2_half"] for c in comparisons
                                                              if c["b"] == "r1_attacker"), None),
               "regression_rate_below_5pct": (reg < 0.05) if reg is not None else None,
               "blind_acceptance": "needs two teammates: cc rq2 --acceptance-sheet, then cc rq2-kappa"},
        "pending_batch_items": pending,
        "usage": usage_report(llm), "evaluator_usage": usage_report(evaluator_llm),
        "config": {"systems": list(systems), "max_rounds": max_rounds, "token_budget": token_budget,
                   "n_ndas": len(docs), "evaluator": evaluator_llm.name, "attacker": (attacker_llm or llm).name},
    }
    if noise_floor:
        drafts = [planted[i].draft for i in docs]
        deal_of = {planted[i].draft.id: planted[i].deal for i in docs}
        rules = list(gold_by_company[planted[docs[0]].deal.company].rules) if docs else []
        try:
            metrics["evaluator_noise_floor"] = ev.noise_floor(drafts, rules, deal_of, n=noise_floor, seed=seed)
        except PendingBatch:  # batch mode: the judge's repeat checks are queued with the rest
            metrics["pending_batch_items"] += 1
    out = run_dir(f"rq2-{llm.name}", out_root)
    write_jsonl(out / "repairs.jsonl", rows)
    write_jsonl(out / "detections.jsonl", detections)
    write_jsonl(out / "repaired_drafts.jsonl", drafts_out)  # every repaired NDA, scored or still pending
    (out / "metrics.json").write_text(json.dumps(metrics, indent=1, default=str))
    metrics["out_dir"] = str(out)
    return metrics


# ------------------------------------------------------------------ blind acceptance (two teammates)

def acceptance_sheet(repairs_jsonl: str | Path, out_csv: str | Path, n_ndas: int = 50, seed: int = 0) -> Path:
    """One row per redline from a random 50 NDAs, systems hidden and shuffled. The key file
    (<out>.key.json) maps item ids back to systems; raters never see it."""
    rows = [json.loads(l) for l in Path(repairs_jsonl).read_text().splitlines() if l.strip()]
    rng = random.Random(seed)
    docs = sorted({r["doc_id"] for r in rows})
    keep = set(rng.sample(docs, min(n_ndas, len(docs))))
    items = [(r["system"], r["doc_id"], e) for r in rows if r["doc_id"] in keep for e in r["edits"]]
    rng.shuffle(items)
    key = {}
    out = Path(out_csv)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["item", "nda", "op", "original_clause", "redline", "accept (y/n)", "comment"])
        for k, (sysname, doc, e) in enumerate(items, 1):
            iid = f"R{k:04d}"
            key[iid] = sysname
            w.writerow([iid, doc, e["op"], e["before"] if e["op"] != "insert_after" else "(new clause)",
                        e["text"] or "(delete)", "", ""])
    out.with_suffix(".key.json").write_text(json.dumps(key, indent=1))
    return out


def acceptance_kappa(sheet_a: str | Path, sheet_b: str | Path, key_path: str | Path) -> dict:
    """Acceptance rate per system (both raters' mean) and Cohen's kappa between the two raters."""
    def read(p):
        with Path(p).open() as f:
            return {r["item"]: r["accept (y/n)"].strip().lower().startswith("y") for r in csv.DictReader(f)
                    if r["accept (y/n)"].strip()}
    a, b = read(sheet_a), read(sheet_b)
    key = json.loads(Path(key_path).read_text())
    both = sorted(set(a) & set(b))
    per = {}
    for s in sorted(set(key.values())):
        ids = [i for i in both if key.get(i) == s]
        if ids:
            per[s] = {"n": len(ids), "accept_rate": round(sum(a[i] + b[i] for i in ids) / (2 * len(ids)), 4)}
    return {"n_items": len(both), "kappa": cohen_kappa([a[i] for i in both], [b[i] for i in both]),
            "per_system": per, "h2_loop_accept_70pct": per.get("loop", {}).get("accept_rate", 0) >= 0.7}
