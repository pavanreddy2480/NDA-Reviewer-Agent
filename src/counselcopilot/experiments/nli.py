"""ContractNLI with the rule-check primitive: retrieve top-k spans for a hypothesis, then
classify. This is the "prompted model" row of the fine-tuning comparison (design §6, §8.3)
and the quickest test that a backend and the checker prompt work."""

from __future__ import annotations

import json

from ..data.contractnli import HELD_OUT_HYPOTHESES, ContractNLI
from ..data.draft import Draft
from ..eval.metrics import evidence_recall, nli_metrics
from ..llm import LLMClient
from ..retrieval.index import HybridIndex, Passage
from ..review.checker import run_check
from .common import run_dir, usage_report, write_jsonl


def resolve_hypotheses(data: ContractNLI, spec: str) -> list[str]:
    if spec == "all":
        return data.hypothesis_keys
    if spec == "held_out":
        return list(HELD_OUT_HYPOTHESES)
    if spec == "train":
        return data.train_hypotheses()
    return [h.strip() for h in spec.split(",")]


def run_nli(llm: LLMClient, data: ContractNLI, split: str = "dev", hypotheses: str = "all",
            limit: int | None = None, k: int = 12, whole_doc: bool = False, max_workers: int = 8,
            out_root: str = "runs") -> dict:
    docs = data[split][:limit] if limit else data[split]
    hyps = resolve_hypotheses(data, hypotheses)
    jobs = []
    for doc in docs:
        draft = Draft.from_nda(doc)
        index = HybridIndex([Passage(str(i), s) for i, s in enumerate(draft.segments)])
        for h in hyps:
            jobs.append((doc, draft, index, h))

    def one(job):
        doc, draft, index, h = job
        text = data.hypotheses[h].text
        ids = (list(range(len(draft.segments))) if whole_doc
               else sorted(int(x.passage.id) for x in index.search(text, k=k)))
        res = run_check(llm, text, draft, ids, tag="nli")
        a = doc.annotations[h]
        return {"doc_id": doc.id, "hypothesis": h, "gold": a.label.value, "pred": res.label,
                "gold_spans": list(a.spans), "pred_spans": res.evidence, "shown": res.shown,
                "confidence": res.confidence, "rationale": res.rationale, "error": res.error}

    rows = llm.map(one, jobs, max_workers)
    metrics = {"all": nli_metrics([r["gold"] for r in rows], [r["pred"] for r in rows])}
    metrics["all"]["retrieval_evidence_recall"] = evidence_recall(
        [tuple(r["gold_spans"]) for r in rows], [r["shown"] for r in rows])
    for h in hyps:
        sub = [r for r in rows if r["hypothesis"] == h]
        metrics[h] = nli_metrics([r["gold"] for r in sub], [r["pred"] for r in sub])
        metrics[h]["held_out"] = h in HELD_OUT_HYPOTHESES
    metrics["errors"] = sum(1 for r in rows if r["error"])
    metrics["usage"] = usage_report(llm)
    metrics["config"] = {"split": split, "hypotheses": hyps, "n_docs": len(docs), "k": k, "whole_doc": whole_doc}

    out = run_dir(f"nli-{split}-{llm.name}", out_root)
    write_jsonl(out / "predictions.jsonl", rows)
    (out / "metrics.json").write_text(json.dumps(metrics, indent=1))
    metrics["out_dir"] = str(out)
    return metrics
