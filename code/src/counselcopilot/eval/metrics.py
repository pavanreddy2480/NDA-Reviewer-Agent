"""Detection metrics (design §8.3) and ContractNLI NLI metrics."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass

import numpy as np

from ..benchmark.gold import GoldNDA
from ..review.findings import Finding


@dataclass
class PRF:
    tp: int = 0
    fp: int = 0
    fn: int = 0

    @property
    def precision(self) -> float:
        return self.tp / (self.tp + self.fp) if self.tp + self.fp else 0.0

    @property
    def recall(self) -> float:
        return self.tp / (self.tp + self.fn) if self.tp + self.fn else 0.0

    @property
    def f1(self) -> float:
        p, r = self.precision, self.recall
        return 2 * p * r / (p + r) if p + r else 0.0

    def as_dict(self) -> dict:
        return {"tp": self.tp, "fp": self.fp, "fn": self.fn, "precision": round(self.precision, 4),
                "recall": round(self.recall, 4), "f1": round(self.f1, 4)}


def _citation_ok(pred: Finding, gold_evidence: tuple[int, ...]) -> bool:
    if not gold_evidence:  # omissions, or gold without spans
        return True
    return bool(set(pred.evidence) & set(gold_evidence))


def score_detection(preds: dict[int, list[Finding]], golds: dict[int, GoldNDA],
                    strict_citations: bool = True, only_scored_rules: bool = True,
                    origin: str | None = None, lenient_type: bool = False, ci: bool = True) -> dict:
    """Micro P/R/F1 overall and per defect type, plus false alarms per NDA.

    A prediction is a true positive when (rule, type) matches a gold defect and, with
    `strict_citations`, it cites at least one gold evidence segment (defects without gold
    evidence, i.e. omissions and field rules, pass this check: `n_gold_with_evidence` says how
    many defects the strict check applies to). Predictions on unscored rules are ignored when
    `only_scored_rules`. `origin` ("natural" / "planted") scores one subset: predictions that
    match a gold defect of the other origin are ignored, not counted as false alarms.
    `lenient_type` matches on the rule alone (a violation reported as approval-needed still
    counts); type accuracy is then reported separately. `ci`: 95% bootstrap CIs over NDAs.
    """
    overall, per_type = PRF(), defaultdict(PRF)
    per_doc: list[tuple[int, int, int]] = []
    per_doc_fp: list[int] = []
    type_ok = type_n = 0

    def key(rule_id: str, t: str):
        return rule_id if lenient_type else (rule_id, t)

    for doc_id, g in golds.items():
        all_gold = {key(d.rule_id, d.type.value): d for d in g.defects}
        gold = {k: d for k, d in all_gold.items() if origin is None or d.origin == origin}
        scored = set(g.scored_rules) | {d.rule_id for d in g.defects}
        tp = fp = 0
        matched = set()
        for f in preds.get(doc_id, []):
            if only_scored_rules and f.rule_id not in scored and f.rule_id in g.unscored_rules:
                continue
            k = key(f.rule_id, f.type.value)
            if k in all_gold and k not in gold:
                continue  # a defect of the other origin
            gd = gold.get(k)
            if gd is not None and k not in matched and (not strict_citations or _citation_ok(f, gd.evidence)):
                tp += 1
                per_type[gd.type.value].tp += 1
                matched.add(k)
                type_n += 1
                type_ok += f.type == gd.type
            else:
                fp += 1
                per_type[f.type.value].fp += 1
        fn = 0
        for k in gold.keys() - matched:
            fn += 1
            per_type[gold[k].type.value].fn += 1
        overall.tp, overall.fp, overall.fn = overall.tp + tp, overall.fp + fp, overall.fn + fn
        per_doc.append((tp, fp, fn))
        per_doc_fp.append(fp)
    out = {
        "overall": overall.as_dict(),
        "by_type": {t: v.as_dict() for t, v in sorted(per_type.items())},
        "false_alarms_per_nda": round(float(np.mean(per_doc_fp)) if per_doc_fp else 0.0, 3),
        "n_ndas": len(golds),
        "n_gold_defects": sum(1 for g in golds.values() for d in g.defects if origin is None or d.origin == origin),
        "n_gold_with_evidence": sum(1 for g in golds.values() for d in g.defects
                                    if d.evidence and (origin is None or d.origin == origin)),
        "per_doc": per_doc,
    }
    if lenient_type:
        out["type_accuracy"] = round(type_ok / type_n, 4) if type_n else None
    if ci:
        out["ci95"] = bootstrap_prf(per_doc)
    return out


def _prf(rows: np.ndarray) -> np.ndarray:
    tp, fp, fn = rows[..., 0], rows[..., 1], rows[..., 2]
    with np.errstate(divide="ignore", invalid="ignore"):
        p = np.where(tp + fp > 0, tp / (tp + fp), 0.0)
        r = np.where(tp + fn > 0, tp / (tp + fn), 0.0)
        f = np.where(p + r > 0, 2 * p * r / (p + r), 0.0)
    return np.stack([p, r, f], axis=-1)


def bootstrap_prf(per_doc: list[tuple[int, int, int]], n: int = 2000, seed: int = 0, alpha: float = 0.05) -> dict:
    """95% CIs of micro precision/recall/F1: resample NDAs, re-sum tp/fp/fn per resample."""
    if not per_doc:
        return {}
    arr = np.asarray(per_doc, dtype=float)
    idx = np.random.default_rng(seed).integers(0, len(arr), size=(n, len(arr)))
    stats = _prf(arr[idx].sum(axis=1))
    lo, hi = np.quantile(stats, alpha / 2, axis=0), np.quantile(stats, 1 - alpha / 2, axis=0)
    return {m: [round(float(lo[i]), 4), round(float(hi[i]), 4)] for i, m in enumerate(("precision", "recall", "f1"))}


def paired_bootstrap(per_doc_a: list[tuple[int, int, int]], per_doc_b: list[tuple[int, int, int]],
                     metric: str = "recall", n: int = 5000, seed: int = 0, margin: float | None = None) -> dict:
    """Difference A - B of a micro metric with the same NDA resamples for both systems (paired).
    With `margin` (e.g. 0.03), also the equivalence test (TOST at 5%): A and B are equivalent
    when the 90% CI of the difference lies inside (-margin, +margin). H1's "within 3 points"."""
    a, b = np.asarray(per_doc_a, dtype=float), np.asarray(per_doc_b, dtype=float)
    assert len(a) == len(b), "systems must be scored on the same NDAs, in the same order"
    i = ("precision", "recall", "f1").index(metric)
    idx = np.random.default_rng(seed).integers(0, len(a), size=(n, len(a)))
    diff = _prf(a[idx].sum(axis=1))[:, i] - _prf(b[idx].sum(axis=1))[:, i]
    point = float(_prf(a.sum(axis=0))[i] - _prf(b.sum(axis=0))[i])
    out = {"metric": metric, "diff": round(point, 4),
           "ci95": [round(float(np.quantile(diff, 0.025)), 4), round(float(np.quantile(diff, 0.975)), 4)],
           "p_a_not_better": round(float(np.mean(diff <= 0)), 4)}
    if margin is not None:
        lo, hi = float(np.quantile(diff, 0.05)), float(np.quantile(diff, 0.95))
        out["equivalent_within_margin"] = bool(-margin < lo and hi < margin)
        out["ci90"] = [round(lo, 4), round(hi, 4)]
    return out


def bootstrap_ci(values: list[float], n: int = 2000, seed: int = 0, alpha: float = 0.05) -> tuple[float, float]:
    """95% bootstrap CI of a per-NDA mean (e.g. false alarms per NDA)."""
    if not values:
        return (0.0, 0.0)
    rng = np.random.default_rng(seed)
    arr = np.asarray(values, dtype=float)
    means = rng.choice(arr, size=(n, len(arr)), replace=True).mean(axis=1)
    return float(np.quantile(means, alpha / 2)), float(np.quantile(means, 1 - alpha / 2))


def nli_metrics(gold: list[str], pred: list[str], labels=("Entailment", "Contradiction", "NotMentioned")) -> dict:
    acc = float(np.mean([g == p for g, p in zip(gold, pred)])) if gold else 0.0
    f1s = {}
    for lab in labels:
        tp = sum(g == lab and p == lab for g, p in zip(gold, pred))
        fp = sum(g != lab and p == lab for g, p in zip(gold, pred))
        fn = sum(g == lab and p != lab for g, p in zip(gold, pred))
        f1s[lab] = PRF(tp, fp, fn).f1
    present = [l for l in labels if any(g == l for g in gold)]
    return {
        "accuracy": round(acc, 4),
        "macro_f1": round(float(np.mean([f1s[l] for l in present])) if present else 0.0, 4),
        "f1_by_label": {k: round(v, 4) for k, v in f1s.items()},
        "confusion": dict(Counter(f"{g}->{p}" for g, p in zip(gold, pred))),
        "n": len(gold),
    }


def evidence_recall(gold_spans: list[tuple[int, ...]], shown: list[list[int]]) -> float:
    """Share of labelled (non-NotMentioned) items whose gold evidence was retrieved at all.
    This is the retrieval ceiling for omission checks: a clause that isn't retrieved looks absent."""
    vals = [bool(set(g) & set(s)) for g, s in zip(gold_spans, shown) if g]
    return round(float(np.mean(vals)), 4) if vals else 0.0


def cohen_kappa(a: list, b: list) -> float:
    """Agreement between two raters (human vs human, or human vs the evaluator model)."""
    if len(a) != len(b):
        raise ValueError("both raters must label the same items")
    if not a:
        return 0.0
    labels = sorted(set(a) | set(b), key=str)
    n = len(a)
    po = sum(x == y for x, y in zip(a, b)) / n
    pe = sum((a.count(l) / n) * (b.count(l) / n) for l in labels)
    return round((po - pe) / (1 - pe), 4) if pe < 1 else 1.0


def _fact(v):
    """Comparable form of a deal fact; None when the label carries no information."""
    from ..benchmark.gold import known
    from ..policy.jurisdictions import normalise_jurisdiction

    if isinstance(v, bool):
        return v
    if v is None or (isinstance(v, str) and v.strip().lower() in ("unknown", "none", "blank")):
        return "none"  # the NDA does not say
    return normalise_jurisdiction(str(v)) if known(v) else None


def fact_accuracy(inferred: dict[int, list], labels: dict[int, dict]) -> dict:
    """Accuracy of deal facts the reviewer read from the NDA (the applicability reasoning step)
    against the labels (after planting: pass each NDA's labels with the planter's updates).
    Labels that are unknown or disputed are skipped; "the NDA doesn't say" counts as a value."""
    out: dict[str, list[bool]] = defaultdict(list)
    for doc_id, facts in inferred.items():
        lab = labels.get(doc_id, {})
        for f in facts:
            raw = lab.get(f.name)
            if raw is None or (isinstance(raw, str) and raw.strip().lower() in ("unknown", "disputed", "blank")):
                continue
            out[f.name].append(_fact(f.value) == _fact(raw))
    return {k: {"accuracy": round(float(np.mean(v)), 4), "n": len(v)} for k, v in out.items()}
