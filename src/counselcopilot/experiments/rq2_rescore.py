"""Score saved RQ2 repairs without re-running the repair systems.

`cc rq2` saves every repaired NDA to repaired_drafts.jsonl before the judge scores it. This module
rebuilds each system's RepairResult from that file (round by round: each round's redlines index
into the draft the previous round left) and scores it with the independent evaluator, exactly as
`run_rq2` would (experiments/rq2.py: score_one, aggregate, paired_remaining). The repair model and
its cache are not needed, so a teammate can judge another machine's repairs.

What the saved file does not hold, and so is not reported: the attacker's scenarios (attacker
loophole recall and precision) and the tokens each system spent.

Batch mode works as for `cc rq2`: give the evaluator a --batch-queue, answer it (Gemini Batch API
or Claude agents), load the answers, run again until nothing is pending. `--originals-only` asks only
the judge's questions about the unrepaired planted NDAs (shared by every system), so they can be
answered once before the per-system queues are made.
"""

from __future__ import annotations

import json
from pathlib import Path

from ..benchmark.gold import gold_deal
from ..benchmark.labels import load_labels
from ..benchmark.planter import PlantedNDA
from ..data.draft import Draft, Edit
from ..eval.evaluator import IndependentEvaluator
from ..llm import LLMClient, PendingBatch
from ..policy.schema import LawPack, PolicyPack
from ..repair.loop import RepairResult, RoundLog
from .common import run_dir, usage_report, write_jsonl
from .rq2 import aggregate, paired_remaining, score_one


def load_repaired(path: str | Path) -> list[dict]:
    return [json.loads(l) for l in Path(path).read_text(encoding="utf-8").splitlines() if l.strip()]


def rebuild(row: dict, original: Draft) -> RepairResult:
    """The RepairResult a saved row came from. Raises ValueError if replaying the redlines does not
    give the saved repaired text (the row does not belong to this planted NDA)."""
    if list(original.segments) != list(row["original"]):
        raise ValueError(f"NDA {row['doc_id']}: the saved original is not the planted draft")
    base, rounds = original, []
    by_round: dict[int, list[Edit]] = {}
    for e in row["edits"]:
        by_round.setdefault(e["round"], []).append(Edit(e["op"], e["segment"], e.get("text", ""), e.get("fixes", "")))
    for k in range(1, row["rounds"] + 1):
        edits = by_round.get(k, [])
        rounds.append(RoundLog(round=k, base=base, edits=edits))
        base = base.apply(edits)
    if list(base.segments) != list(row["repaired"]):
        raise ValueError(f"NDA {row['doc_id']} {row['system']}: replaying the redlines does not give the saved draft")
    return RepairResult(system=row["system"], original=original, final=base, rounds=rounds, stopped=row["stopped"])


def rescore_rq2(repaired_path: str | Path, planted: dict[int, PlantedNDA], gold_packs: list[PolicyPack],
                evaluator_llm: LLMClient, law_pack: LawPack | None = None, labels_path: str | None = None,
                allow_auto_labels: bool = False, hypotheses: dict[str, str] | None = None,
                systems: tuple[str, ...] | None = None, originals_only: bool = False,
                out_root: str = "runs", noise_floor: int = 0, nli_docs=None, nli_n: int = 0,
                seed: int = 0) -> dict:
    gold_by_company = {p.company: p for p in gold_packs}
    labels = load_labels(labels_path, allow_auto=allow_auto_labels) if labels_path else {}
    law_rules = law_pack.as_rules() if law_pack else []
    ev = IndependentEvaluator(evaluator_llm)
    saved = [r for r in load_repaired(repaired_path) if systems is None or r["system"] in systems]
    rows, pending = [], 0
    if originals_only:
        docs = sorted({r["doc_id"] for r in saved})
        for doc_id in docs:
            p = planted[doc_id]
            deal = gold_deal(p.deal, {**labels.get(doc_id, {}), **p.label_updates})
            rules = [r for r in list(gold_by_company[p.deal.company].rules) + law_rules if r.applies_to(deal)]
            try:
                ev._check_all([(r, p.draft, 0) for r in rules])
            except PendingBatch:
                pending += 1
        return {"originals": len(docs), "pending_batch_items": pending}
    for row in saved:
        p = planted[row["doc_id"]]
        res = rebuild(row, p.draft)
        deal = gold_deal(p.deal, {**labels.get(row["doc_id"], {}), **p.label_updates})
        eval_rules = list(gold_by_company[p.deal.company].rules) + law_rules
        try:
            rows.append(score_one(ev, res, p, eval_rules, deal, hypotheses))
        except PendingBatch:
            pending += 1
    extra = {}
    if noise_floor:  # the judge asked twice (seeds 0 and 1) about the same unrepaired NDA and rule
        ids = sorted({r["doc_id"] for r in saved})
        drafts = [planted[i].draft for i in ids]
        deal_of = {planted[i].draft.id: gold_deal(planted[i].deal, {**labels.get(i, {}), **planted[i].label_updates})
                   for i in ids}
        rules_of = {planted[i].draft.id: list(gold_by_company[planted[i].deal.company].rules) + law_rules for i in ids}
        try:
            extra["evaluator_noise_floor"] = ev.noise_floor(drafts, rules_of, deal_of, n=noise_floor, seed=seed)
        except PendingBatch:
            pending += 1
    if nli_n and nli_docs is not None and hypotheses:  # the judge against ContractNLI expert labels
        try:
            extra["evaluator_contractnli"] = ev.validate_on_contractnli(nli_docs, hypotheses, n=nli_n, seed=seed,
                                                                         per_doc=True)
        except PendingBatch:
            pending += 1
    present = tuple(dict.fromkeys(r["system"] for r in saved))
    agg = aggregate(rows)
    comparisons = [c for c in (paired_remaining(rows, "loop", b) for b in present if b != "loop") if c]
    reg = agg.get("loop", {}).get("regression_rate")
    metrics = {
        "systems": agg, "comparisons": comparisons,
        "h2": {"remaining_at_most_half_of_r1": next((c["h2_half"] for c in comparisons if c["b"] == "r1"), None),
               "remaining_at_most_half_of_r1_attacker": next((c["h2_half"] for c in comparisons
                                                              if c["b"] == "r1_attacker"), None),
               "regression_rate_below_5pct": (reg < 0.05) if reg is not None else None},
        **extra,
        "pending_batch_items": pending,
        "evaluator_usage": usage_report(evaluator_llm),
        "config": {"repaired": str(repaired_path), "systems": list(present), "evaluator": evaluator_llm.name,
                   "n_ndas": len({r["doc_id"] for r in saved}),
                   "not_reported": "attacker scenarios and repair tokens (not in repaired_drafts.jsonl)"},
    }
    if not pending:
        out = run_dir(f"rq2-rescore-{evaluator_llm.name}", out_root)
        write_jsonl(out / "repairs.jsonl", rows)
        (out / "metrics.json").write_text(json.dumps(metrics, indent=1, default=str))
        metrics["out_dir"] = str(out)
    return metrics
