"""Ablation study report (docs/design/ablation-studies.md): every ablation run against the full
system on the same NDAs, with a paired bootstrap per metric and Holm's correction across the
family of ablations, plus the component metrics each ablation is meant to move."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from ..eval.metrics import _prf

# what each RQ1 ablation is expected to change (design doc §2); "up"/"down" vs the full system
EXPECTED = {
    "no_reverse": ("omission recall", "down"),
    "no_filter": ("false alarms per NDA", "up"),
    "no_frames": ("violation recall (field rules)", "down"),
    "no_verifier": ("precision", "down"),
    "fixed_pipeline": ("tokens per NDA", "up"),
    "no_xref": ("approval-needed recall", "down"),
    "no_memory": ("escalations per NDA", "up"),
    "no_tool_agent": ("hand-off precision", "down"),
    "structured_applicability": ("F1 (compiled cards)", "down"),
    "tool_errors": ("recovery rate / F1", "down"),
    "tuned_checker": ("F1 and omission recall", "up"),
}


def _load(run: str | Path) -> dict:
    p = Path(run)
    return json.loads((p / "metrics.json" if p.is_dir() else p).read_text())


def label(m: dict) -> str:
    """Pipeline runs by ablation (`full`, `no_reverse`, ...); reviewer runs as `reviewer:<preset>`;
    baselines by system name (`b1`, `b2`, ...)."""
    s = m.get("system", {})
    name = s.get("name", "reviewer")
    if name == "pipeline":
        return s.get("ablation") or "full"
    if name == "reviewer":
        return f"reviewer:{s.get('preset') or m.get('config', {}).get('preset') or 'full'}"
    return name


def paired_test(per_doc_a, per_doc_b, metric: str = "f1", n: int = 5000, seed: int = 0) -> dict:
    """Paired bootstrap of A - B (same NDA resamples for both) with a two-sided p-value:
    2 * min(share of resamples with diff <= 0, share with diff >= 0). Identical systems get p = 1."""
    a, b = np.asarray(per_doc_a, float), np.asarray(per_doc_b, float)
    i = ("precision", "recall", "f1").index(metric)
    idx = np.random.default_rng(seed).integers(0, len(a), size=(n, len(a)))
    diff = _prf(a[idx].sum(axis=1))[:, i] - _prf(b[idx].sum(axis=1))[:, i]
    point = float(_prf(a.sum(axis=0))[i] - _prf(b.sum(axis=0))[i])
    p = min(1.0, 2 * min(float(np.mean(diff <= 0)), float(np.mean(diff >= 0))))
    return {"diff": round(point, 4), "ci95": [round(float(np.quantile(diff, q)), 4) for q in (0.025, 0.975)],
            "p": round(p, 4)}


def holm(pvals: dict[str, float]) -> dict[str, float]:
    """Holm-Bonferroni adjusted p-values (monotone)."""
    order = sorted(pvals, key=pvals.get)
    m, out, running = len(order), {}, 0.0
    for i, k in enumerate(order):
        running = max(running, min(1.0, (m - i) * pvals[k]))
        out[k] = round(running, 4)
    return out


def _type_recall(m: dict, t: str):
    return m["strict"]["by_type"].get(t, {}).get("recall")


def summary_row(m: dict) -> dict:
    s = m["strict"]
    v, h, t = m.get("verifier") or {}, m.get("handoff") or {}, m.get("tool_calling") or {}
    usage = m.get("usage", {})
    n = max(1, len(s.get("per_doc", [])))
    return {
        "precision": s["overall"]["precision"], "recall": s["overall"]["recall"], "f1": s["overall"]["f1"],
        "omission_recall": _type_recall(m, "omission"), "violation_recall": _type_recall(m, "violation"),
        "approval_recall": _type_recall(m, "approval_needed"),
        "false_alarms_per_nda": s.get("false_alarms_per_nda"), "checks_per_nda": m.get("checks_per_nda"),
        "tokens_per_nda": round(sum(usage.get(k, 0) for k in ("input_tokens_uncached", "output_tokens_uncached",
                                                               "cached_input_tokens", "cached_output_tokens")) / n, 1),
        "verifier_rejection_precision": v.get("rejection_precision"),
        "handoff_precision": h.get("handoff_precision"), "handoff_recall": h.get("handoff_recall"),
        "escalations_per_nda": round(h["n_escalations"] / n, 3) if "n_escalations" in h else None,
        "tool_recovery_rate": t.get("recovery_rate"), "unsafe_attempts": t.get("attempted_unsafe_per_episode"),
    }


def ablation_report(runs: list[str | Path], base: str = "full", metrics=("f1", "recall", "precision"),
                    n_boot: int = 5000) -> dict:
    """Pair every run with the base run (same NDAs, same order) and test the difference. A run may
    be given as NAME=PATH to label it (e.g. tuned_checker=runs/...), otherwise its ablation or
    preset name is used."""
    loaded = {}
    for r in runs:
        name, _, path = str(r).rpartition("=") if "=" in str(r) else ("", "", str(r))
        m = _load(path)
        loaded[name or label(m)] = (path, m)
    if base not in loaded:
        raise SystemExit(f"no run labelled {base!r} among {sorted(loaded)}")
    _, bm = loaded[base]
    out = {"base": base, "n_ndas": len(bm["strict"]["per_doc"]), "rows": {}, "skipped": {}}
    pvals = {mt: {} for mt in metrics}
    for name, (path, m) in loaded.items():
        row = {"run": path, **summary_row(m)}
        if name != base:
            pa, pb = m["strict"]["per_doc"], bm["strict"]["per_doc"]
            if len(pa) != len(pb):
                out["skipped"][name] = "different NDAs from the base run"
                continue
            for mt in metrics:
                t = paired_test(pa, pb, mt, n=n_boot)
                row[f"d_{mt}"], row[f"ci95_{mt}"] = t["diff"], t["ci95"]
                pvals[mt][name] = t["p"]
            row["expected"] = EXPECTED.get(name)
        out["rows"][name] = row
    for mt in metrics:  # the family is the ablations; baselines and presets keep their raw p
        fam = {k: v for k, v in pvals[mt].items() if k in EXPECTED}
        for name, p in {**pvals[mt], **holm(fam)}.items():
            out["rows"][name][f"p_holm_{mt}" if name in fam else f"p_{mt}"] = p
    return out


def _p(p, adjusted: bool) -> str:
    if p is None:
        return "—"
    txt = "<0.001" if p < 0.001 else f"{p:.3f}"
    return txt if adjusted else f"{txt} (raw)"


def report_markdown(rep: dict) -> str:
    cols = ["P", "R", "F1", "ΔF1 (95% CI)", "p (Holm)", "Omission R", "FA/NDA", "Tokens/NDA", "Expected effect"]
    lines = [f"Base: `{rep['base']}`, {rep['n_ndas']} NDAs, paired bootstrap, Holm-corrected over the ablations.", "",
             "| Ablation | " + " | ".join(cols) + " |", "|---" * (len(cols) + 1) + "|"]
    for name, r in sorted(rep["rows"].items(), key=lambda kv: (kv[0] != rep["base"], kv[0])):
        d = f"{r['d_f1']:+.3f} [{r['ci95_f1'][0]:+.3f}, {r['ci95_f1'][1]:+.3f}]" if "d_f1" in r else "—"
        exp = f"{r['expected'][0]} {r['expected'][1]}" if r.get("expected") else ""
        lines.append(f"| {name} | {r['precision']} | {r['recall']} | {r['f1']} | {d} | {_p(r.get('p_holm_f1', r.get('p_f1')), 'p_holm_f1' in r)} | "
                     f"{r['omission_recall']} | {r['false_alarms_per_nda']} | {r['tokens_per_nda']} | {exp} |")
    for k, why in rep["skipped"].items():
        lines.append(f"\nSkipped `{k}`: {why}.")
    return "\n".join(lines)


def rq2_markdown(run: str | Path) -> str:
    """Loop ablations (no attacker, no regression check, 1 round, attacker on another model) and
    baselines against the full loop: ratio of remaining problems per NDA with its paired CI."""
    m = _load(run)
    comp = {c["b"]: c for c in m.get("comparisons", [])}
    lines = [f"RQ2 run `{Path(run).name}` (attacker: {m['config'].get('attacker', '?')}); ratio = loop / system, "
             "below 1 means the full loop leaves fewer problems.", "",
             "| System | Remaining/NDA | Loop ÷ system (95% CI) | Regression rate | Repair success | Loopholes left | Rounds | Tokens/NDA |",
             "|---|---|---|---|---|---|---|---|"]
    for name, s in sorted(m["systems"].items(), key=lambda kv: (kv[0] != "loop", kv[0])):
        c = comp.get(name)
        ratio = f"{c['ratio']} [{c['ratio_ci95'][0]}, {c['ratio_ci95'][1]}]" if c and c.get("ratio_ci95") else "—"
        lines.append(f"| {name} | {s['remaining_per_nda']} | {ratio} | {s['regression_rate']} | {s['repair_success']} | "
                     f"{s['loopholes_left_per_nda']} | {s['rounds_mean']} | {s['tokens_per_nda']} |")
    return "\n".join(lines)
