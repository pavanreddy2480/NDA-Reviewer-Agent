"""RQ1 runner: review benchmark NDAs with one system configuration and score findings
against gold defects (natural, from ContractNLI anchors and hand labels; planted, from a
planter manifest)."""

from __future__ import annotations

import json
from dataclasses import asdict

from ..benchmark.align import align, remap_findings
from ..benchmark.deals import deal_sources, generate_deals
from ..benchmark.gold import gold_for
from ..benchmark.labels import load_labels
from ..benchmark.planter import PlantedNDA
from ..data.contractnli import ContractNLI
from ..data.draft import Draft
from ..eval.metrics import fact_accuracy, score_detection
from ..llm import LLMClient, PendingBatch
from ..policy.schema import DealContext, LawPack, PolicyPack
from ..review.policy_reviewer import PolicyReviewer, ReviewConfig
from .common import run_dir, usage_report, write_jsonl


def run_rq1(llm: LLMClient, data: ContractNLI, packs: list[PolicyPack], split: str = "dev",
            preset: str = "full", limit: int | None = None, deals: dict[int, DealContext] | None = None,
            labels_path: str | None = None, seed: int = 0, out_root: str = "runs", max_workers: int = 8,
            law_pack: LawPack | None = None, planted: dict[int, PlantedNDA] | None = None,
            checker_llm: LLMClient | None = None, temperature: float = 0.0,
            hide_facts: bool = False, allow_unverified_labels: bool = False,
            allow_auto_labels: bool = False, deal_seed: int = 0, gold_packs: list[PolicyPack] | None = None,
            applicability: str = "model") -> dict:
    """`packs` are what the reviewer checks: compiled requirement cards (policy/compiler.py) in the
    main runs. `gold_packs` are the gold rule lists gold is scored on; cards are matched to them
    by quote (benchmark/align.py). Without `gold_packs`, `packs` are gold too (oracle-rules run)."""
    docs = data[split][:limit] if limit else data[split]
    if planted is not None:
        docs = [d for d in docs if d.id in planted]
    by_company = {p.company: p for p in packs}
    gold_by_company = {p.company: p for p in gold_packs} if gold_packs else by_company
    alignments = {c: align(by_company[c], gold_by_company[c]) for c in by_company} if gold_packs else {}
    labels = load_labels(labels_path, allow_unverified_labels, allow_auto_labels)
    # deals depend on deal_seed only, so model seeds (`seed`) don't also redraw the benchmark
    deals = deals or generate_deals([d.id for d in docs], list(by_company), seed=deal_seed, labels=labels)
    cfg = ReviewConfig.preset(preset)
    cfg.max_workers, cfg.temperature, cfg.seed = max_workers, temperature, seed
    cfg.applicability = applicability
    reviewers = {c: PolicyReviewer(llm, p, cfg, law_pack=law_pack, checker_llm=checker_llm)
                 for c, p in by_company.items()}

    preds, golds, inferred, fact_labels, rows, pending, errors = {}, {}, {}, {}, [], 0, 0
    for doc in docs:
        p = planted.get(doc.id) if planted else None
        deal = p.deal if p else deals[doc.id]
        if hide_facts:  # leave facts blank on the form; the reviewer must read them from the NDA
            deal = deal.model_copy(update={"personal_data": None, "governing_law": None})
        draft = p.draft if p else Draft.from_nda(doc)
        lab = dict(labels.get(doc.id, {}))
        if p:
            lab.update(p.label_updates)
        try:
            result = reviewers[deal.company].review(draft, deal)
        except PendingBatch:
            pending += 1
            continue
        preds[doc.id] = (remap_findings(result.findings, alignments[deal.company]) if alignments
                         else result.findings)
        inferred[doc.id] = result.inferred_facts
        fact_labels[doc.id] = lab
        errors += result.n_errors
        golds[doc.id] = gold_for(doc, deal, gold_by_company[deal.company], lab, law_pack,
                                 p.gold_entry() if p else None)
        rows.append({
            "doc_id": doc.id, "deal": result.deal.model_dump(mode="json"),
            "deal_sources": deal_sources(labels.get(doc.id)),
            "inferred_facts": [vars(f) for f in result.inferred_facts],
            "applicable_rules": result.applicable_rules, "undecided_rules": result.undecided_rules,
            "rules_in_scope": result.rules_in_scope,
            "n_checks": result.n_checks, "n_agent_searches": result.n_agent_searches,
            "findings": [f.model_dump(mode="json") for f in result.findings],
            "scored_findings": [f.model_dump(mode="json") for f in preds[doc.id]],  # on gold rule ids
            "applicability_notes": result.applicability_notes,
            "gold": [{"rule_id": d.rule_id, "type": d.type.value, "evidence": list(d.evidence), "origin": d.origin}
                     for d in golds[doc.id].defects],
            "unscored_rules": golds[doc.id].unscored_rules,
            "checks": [{"rule_id": c.rule_id, "direction": c.direction, "label": c.result.label,
                        "evidence": c.result.evidence, "shown": c.result.shown,
                        "confidence": c.result.confidence, "error": c.result.error,
                        "agent": vars(c.agent) if c.agent else None}
                       for c in result.checks],
        })

    def by_origin(origin: str) -> dict:
        m = score_detection(preds, golds, origin=origin)
        return {"overall": m["overall"], "ci95": m["ci95"], "n_gold_defects": m["n_gold_defects"]}

    n_applicable = [len(r["applicable_rules"]) for r in rows]
    metrics = {
        "strict": score_detection(preds, golds, strict_citations=True),
        "lenient": score_detection(preds, golds, strict_citations=False),
        "rule_only": score_detection(preds, golds, strict_citations=False, lenient_type=True),
        "check_errors": errors,
        "checks_per_nda": round(sum(r["n_checks"] for r in rows) / max(len(rows), 1), 2),
        "agent_searches_per_nda": round(sum(r["n_agent_searches"] for r in rows) / max(len(rows), 1), 2),
        # H1's check saving is reported against applicable rules, not the whole pack (review problem 3)
        "applicable_rules_per_nda": round(sum(n_applicable) / max(len(rows), 1), 2),
        "fact_accuracy": fact_accuracy(inferred, fact_labels),
        "pending_batch_ndas": pending,
        # oracle_rules: the reviewer was handed the gold rule list (an upper bound, not the system)
        "rules": "compiled" if gold_packs else "oracle_rules",
        "compiler": {c: a.report(gold_by_company[c]) for c, a in alignments.items()},
        "usage": usage_report(llm),
        "config": {"split": split, "preset": preset, **asdict(cfg), "n_docs": len(docs),
                   "packs": [p.company for p in packs], "law_pack": law_pack.version if law_pack else None,
                   "planted": planted is not None, "hide_facts": hide_facts, "deal_seed": deal_seed,
                   "checker": checker_llm.name if checker_llm else llm.name},
    }
    if planted is not None:
        metrics["planted_only"] = by_origin("planted")
        metrics["natural_only"] = by_origin("natural")
        # injection text changes no gold, so recall on injected NDAs should match the rest
        inj = {i for i in preds if planted[i].injection}
        if inj:
            def subset(ids):
                m = score_detection({i: preds[i] for i in ids}, {i: golds[i] for i in ids}, ci=False)
                return {"overall": m["overall"], "n_ndas": len(ids)}
            metrics["injection"] = {"injected": subset(inj), "clean": subset(set(preds) - inj)}
    if checker_llm is not None:
        metrics["checker_usage"] = usage_report(checker_llm)
    out = run_dir(f"rq1-{preset}-{split}-{llm.name}", out_root)
    write_jsonl(out / "reviews.jsonl", rows)
    (out / "metrics.json").write_text(json.dumps(metrics, indent=1, default=str))
    metrics["out_dir"] = str(out)
    return metrics
