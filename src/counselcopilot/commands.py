"""CLI commands added for the end-to-end system (registered by cli.main):

    cc pipeline --pack P --doc-id N               full CounselCopilot review of one NDA (Figure 1)
    cc rq2 --pack P --planted F --evaluator-backend B   red-team repair loop vs R1, R1+A, R2
    cc rq2-kappa SHEET_A SHEET_B KEY              blind acceptance and Cohen's kappa of two raters
    cc cascade LOCAL_RUN REMOTE_RUN --pack P       local-first cascade, simulated offline
    cc sweep --out DIR                             padded policy corpora for the size sweep
    cc frames silver --backend gemini-flash        silver obligation frames for fine-tuning
    cc finetune data --cuad CUAD_v1.json           QLoRA training mix (NLI + CUAD + frames)
    cc compare RUN_A RUN_B --metric recall          paired bootstrap, TOST with --margin
    cc report RUN...                               one markdown table over RQ1 / RQ2 runs
    cc smoke                                       everything, offline, on a synthetic mini-benchmark
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

COMPANIES = ("saas", "hospital", "manufacturer")


def _law(path):
    from .cli import _law_pack

    return _law_pack(path)


def _policy_dirs(packs, paths) -> dict:
    from .baselines.common import policy_dir_for

    out = {}
    for pack, path in zip(packs, paths):
        d = policy_dir_for(path)
        if d is not None:
            out[pack.company] = str(d)
    return out


def _precedents(args, packs):
    from .agents.memory import PrecedentMemory, scripted_precedents

    if getattr(args, "precedents", None):
        return PrecedentMemory.load(args.precedents).items
    n = getattr(args, "scripted_precedents", 0)
    return scripted_precedents(packs, n) if n else []


# ------------------------------------------------------------------ pipeline (one NDA)

def cmd_pipeline(args) -> None:
    from .agents.memory import PrecedentMemory
    from .agents.pipeline import CounselCopilot, PipelineConfig
    from .cli import _load_data
    from .data.draft import Draft
    from .llm import load_backend
    from .policy.schema import DealContext, PolicyPack

    llm = load_backend(args.backend, args.config, use_cache=not args.no_cache)
    pack = PolicyPack.load(args.pack)
    draft = (Draft.from_text(Path(args.text).read_text(encoding="utf-8"), args.text) if args.text
             else Draft.from_nda(_load_data(args).by_id(args.doc_id)))
    deal = DealContext(company=pack.company, counterparty_type=args.counterparty,
                       personal_data=True if args.personal_data else None, counterparty_country=args.country)
    mem = PrecedentMemory.load(args.precedents) if args.precedents else PrecedentMemory()
    res = CounselCopilot(llm, pack, _law(args.law_pack), PipelineConfig.ablation(args.ablation), memory=mem).review(draft, deal)
    print(f"Plan: {res.plan.reviewers} ({res.plan.rationale})")
    print(f"Deal after reading the NDA: {res.deal.model_dump(mode='json')}\n")
    for f in res.findings + res.unscored_findings:
        mark = {True: "supported", None: "UNCERTAIN -> senior counsel", False: "rejected"}[f.verified]
        print(f"- {f.type.value.upper():<16} {f.rule_id:<20} [{mark}] {f.explanation[:160]}")
        for i in f.evidence[:3]:
            print(f"      [{i}] {draft.segments[i][:160]}")
    rejected = [v for v in res.verdicts if v.verdict == "unsupported"]
    if rejected:
        print(f"\nVerifier rejected {len(rejected)}: " + ", ".join(f"{v.finding.rule_id} ({v.reason[:60]})" for v in rejected))
    if res.handoff:
        for e in res.handoff.escalations:
            print(f"ESCALATED {e.rule_id}: {e.reason} {e.approval_id} {e.note[:80]}")
        for e in res.handoff.resolved:
            print(f"APPROVED BEFORE {e.rule_id}: {e.note[:100]}")
    print(f"\nTokens: {llm.total_usage()}")


# ------------------------------------------------------------------ RQ2

def cmd_rq2(args) -> None:
    from .benchmark.planter import load_planted
    from .experiments.rq2 import acceptance_sheet, run_rq2
    from .llm import load_backend
    from .policy.schema import PolicyPack

    if args.acceptance_sheet:
        print(acceptance_sheet(args.acceptance_sheet, args.sheet_out, args.n_sheet))
        return
    llm = load_backend(args.backend, args.config, use_cache=not args.no_cache)
    # --evaluator-batch-queue: the repair systems run live, but every uncached judge request is stored
    # in the queue instead of being sent. Answer the queue later (cc batch submit/collect, or export/load),
    # then rerun the same command: repairs come from the cache and scoring finishes.
    ev = load_backend(args.evaluator_backend, args.config, use_cache=not args.no_cache,
                      batch_queue=args.evaluator_batch_queue)
    checker = load_backend(args.checker_backend, args.config) if args.checker_backend else None
    attacker = load_backend(args.attacker_backend, args.config) if args.attacker_backend else None
    hyps = None
    if not args.no_hypotheses:
        try:
            from .cli import _load_data

            d = _load_data(args, ("test",))
            hyps = {k: h.text for k, h in d.hypotheses.items()}
        except FileNotFoundError:
            print("ContractNLI not found: natural loopholes are not re-checked", file=sys.stderr)
    m = run_rq2(llm, [PolicyPack.load(p) for p in args.pack], load_planted(args.planted), ev,
                _law(args.law_pack), tuple(args.systems), checker, attacker,
                [PolicyPack.load(p) for p in args.gold_pack] if args.gold_pack else None,
                args.labels, args.allow_auto, hyps, args.limit, args.max_rounds, args.token_budget,
                noise_floor=args.noise_floor)
    print(json.dumps({k: m[k] for k in ("systems", "comparisons", "h2", "pending_batch_items", "out_dir")},
                     indent=1, default=str))
    if m["pending_batch_items"]:
        print(f"{m['pending_batch_items']} system runs wait on judge answers in the queue; answer it "
              "(cc batch), load the answers and run this command again.", file=sys.stderr)


def cmd_rq2_kappa(args) -> None:
    from .experiments.rq2 import acceptance_kappa

    print(json.dumps(acceptance_kappa(args.sheet_a, args.sheet_b, args.key), indent=1))


# ------------------------------------------------------------------ cascade, sweep

def cmd_cascade(args) -> None:
    from .experiments.cascade import pick_threshold, simulate_cascade
    from .policy.schema import PolicyPack

    out = simulate_cascade(args.local, args.remote, [PolicyPack.load(p) for p in args.pack], _law(args.law_pack),
                           [PolicyPack.load(p) for p in args.gold_pack] if args.gold_pack else None,
                           escalate_high_severity=args.high_severity, second_local_run=args.second_local,
                           remote_cost_per_check=args.cost_per_check)
    out["chosen"] = pick_threshold(out["curve"], args.max_f1_drop)
    print(json.dumps(out, indent=1))


def cmd_sweep(args) -> None:
    from .experiments.sweep import sweep_plan
    from .policy.schema import PolicyPack

    comp = {}
    for c in COMPANIES:
        pack = PolicyPack.load(f"packs/policynda/{c}/gold_rules.yaml")
        comp[pack.company] = f"packs/policynda/{c}/policies"
    plan = sweep_plan(comp, args.out, tuple(args.sizes), args.padding or None)
    print(json.dumps(plan, indent=1))
    print("Next: cc compile each padded folder, then cc rq1 --system b1 and --system pipeline on the 40-NDA subset.",
          file=sys.stderr)


# ------------------------------------------------------------------ fine-tuning

def cmd_frames(args) -> None:
    from .cli import _load_data
    from .finetune.data import silver_frames
    from .llm import load_backend

    llm = load_backend(args.backend, args.config, use_cache=not args.no_cache)
    n = silver_frames(llm, _load_data(args, (args.split,)), args.out, args.split, args.limit)
    print(f"{n} NDAs of silver frames in {args.out}")


def cmd_finetune(args) -> None:
    from .cli import _load_data
    from .finetune.data import build_all, cuad_examples, frame_examples, load_cuad, nli_examples

    nli = nli_examples(_load_data(args, ("train",)), "train", limit=args.limit)
    cuad = cuad_examples(load_cuad(args.cuad)) if args.cuad else []
    frames = frame_examples(args.frames) if args.frames else []
    print(json.dumps(build_all(args.out, nli, cuad, frames, max_per_task=args.max_per_task), indent=1))


# ------------------------------------------------------------------ comparing and reporting runs

def _metrics(run) -> dict:
    p = Path(run)
    return json.loads((p / "metrics.json" if p.is_dir() else p).read_text())


def cmd_compare(args) -> None:
    from .eval.metrics import paired_bootstrap

    a, b = _metrics(args.run_a), _metrics(args.run_b)
    key = args.score
    pa, pb = a[key]["per_doc"], b[key]["per_doc"]
    if len(pa) != len(pb):
        sys.exit("runs scored different numbers of NDAs; compare runs on the same split, deals and limit")
    print(json.dumps(paired_bootstrap(pa, pb, args.metric, margin=args.margin), indent=1))


def report_table(runs: list[str]) -> str:
    rq1, rq2 = [], []
    for r in runs:
        m = _metrics(r)
        if "systems" in m and "comparisons" in m:
            rq2.append((r, m))
        else:
            rq1.append((r, m))
    out = []
    if rq1:
        out += ["| Run | System | P | R | F1 | Omission R | FA/NDA | Checks/NDA | $ full |", "|---|---|---|---|---|---|---|---|---|"]
        for r, m in rq1:
            s = m["strict"]
            om = s["by_type"].get("omission", {}).get("recall", "")
            sysname = m.get("system", {}).get("name", "reviewer")
            label = (m.get("system", {}).get("ablation") or m.get("system", {}).get("preset")
                     or (m["config"].get("preset") if sysname == "reviewer" else ""))
            out.append(f"| {Path(r).name} | {sysname}{':' + label if label else ''} | {s['overall']['precision']} | {s['overall']['recall']} | "
                       f"{s['overall']['f1']} | {om} | {s['false_alarms_per_nda']} | {m['checks_per_nda']} | "
                       f"{m['usage']['cost_usd_full']} |")
    if rq2:
        out += ["", "| Run | System | Remaining/NDA | Regression rate | Repair success | Loopholes left | Rounds | Tokens/NDA |",
                "|---|---|---|---|---|---|---|---|"]
        for r, m in rq2:
            for name, s in m["systems"].items():
                out.append(f"| {Path(r).name} | {name} | {s['remaining_per_nda']} | {s['regression_rate']} | "
                           f"{s['repair_success']} | {s['loopholes_left_per_nda']} | {s['rounds_mean']} | {s['tokens_per_nda']} |")
    return "\n".join(out)


def cmd_report(args) -> None:
    text = report_table(args.runs)
    if args.out:
        Path(args.out).write_text(text + "\n")
    print(text)


# ------------------------------------------------------------------ smoke: everything, offline

def run_smoke(out_root: str = "runs/smoke", backend: str = "heuristic", judge: str = "heuristic-judge",
              config: str | None = None, seed: int = 0) -> dict:
    """Every experiment of the proposal on a synthetic mini-benchmark with an offline backend:
    a plumbing check of the whole system. Its numbers are not results."""
    import yaml

    from .agents.memory import scripted_precedents
    from .benchmark.deals import generate_deals
    from .benchmark.planter import Planter, plant_split, save_planted
    from .benchmark.synthetic import synthetic_contractnli
    from .experiments.cascade import simulate_cascade
    from .experiments.nli import run_nli
    from .experiments.rq1 import run_rq1
    from .experiments.rq2 import SYSTEMS, acceptance_sheet, run_rq2
    from .llm import load_backend
    from .policy.schema import LawPack, PolicyPack

    out = Path(out_root)
    out.mkdir(parents=True, exist_ok=True)
    data, labels = synthetic_contractnli(seed=seed)
    lp = out / "labels.yaml"
    lp.write_text(yaml.safe_dump(labels))
    paths = [f"packs/policynda/{c}/gold_rules.yaml" for c in COMPANIES]
    packs = [PolicyPack.load(p) for p in paths]
    law = LawPack.load("packs/law/us_law_pack.yaml")
    dirs = _policy_dirs(packs, paths)
    prec = scripted_precedents(packs, 30)
    llm = load_backend(backend, config)
    runs, summary = [], {}
    m = run_nli(llm, data, "dev", out_root=str(out))
    summary["nli"] = {"accuracy": m["all"]["accuracy"], "macro_f1": m["all"]["macro_f1"]}
    for system, extra in [("reviewer", {"preset": "full"}), ("reviewer", {"preset": "no_reverse"}),
                          ("reviewer", {"preset": "exhaustive_filtered"}), ("pipeline", {"ablation": "full"}),
                          ("pipeline", {"ablation": "no_verifier"}), ("pipeline", {"ablation": "fixed_pipeline"}),
                          ("pipeline", {"ablation": "tool_errors"}), ("b1", {}), ("b2", {}), ("b2_checklist", {}), ("b3", {})]:
        m = run_rq1(llm, data, packs, "test", law_pack=law, labels_path=str(lp), system=system, out_root=str(out),
                    policy_dirs=dirs, precedents=prec, max_workers=4, hide_facts=True, **extra)
        runs.append(m["out_dir"])
    deals = generate_deals([d.id for d in data["test"]], [p.company for p in packs], labels=labels)
    planted = plant_split({p.company: Planter(p, law) for p in packs}, data["test"], deals, labels, seed,
                          n_state_law=4, n_injection=4)
    save_planted(planted, out / "planted.json")
    planted = {p.doc_id: p for p in planted}
    m = run_rq1(llm, data, packs, "test", law_pack=law, labels_path=str(lp), planted=planted, system="pipeline",
                out_root=str(out), precedents=prec, max_workers=4)
    runs.append(m["out_dir"])
    summary["injection"] = m.get("injection")
    hyps = {k: h.text for k, h in data.hypotheses.items()}
    m2 = run_rq2(llm, packs, planted, load_backend(judge, config), law, SYSTEMS, labels_path=str(lp),
                 hypotheses=hyps, out_root=str(out), noise_floor=10)
    runs.append(m2["out_dir"])
    acceptance_sheet(Path(m2["out_dir"]) / "repairs.jsonl", out / "acceptance_sheet.csv", 50)
    summary["cascade"] = simulate_cascade(runs[0], runs[0], packs, law)["curve"][:2]
    table = report_table(runs)
    (out / "SMOKE.md").write_text("# Smoke run (synthetic data, offline heuristic backend: plumbing only, not results)\n\n"
                                  + table + "\n")
    summary["runs"] = runs
    summary["table"] = str(out / "SMOKE.md")
    return summary


def cmd_smoke(args) -> None:
    print(json.dumps(run_smoke(args.out, args.backend, args.judge, args.config), indent=1, default=str))


# ------------------------------------------------------------------ registration

def register(sub, llm_args) -> None:
    from .agents.pipeline import PipelineConfig
    from .experiments.rq2 import SYSTEMS

    pp = sub.add_parser("pipeline", help="full CounselCopilot review of one NDA (planner, reviewers, verifier, hand-off)")
    llm_args(pp)
    pp.add_argument("--pack", required=True)
    g = pp.add_mutually_exclusive_group(required=True)
    g.add_argument("--doc-id", type=int)
    g.add_argument("--text")
    pp.add_argument("--counterparty", default="vendor", choices=["vendor", "customer", "employee", "partner"])
    pp.add_argument("--personal-data", action="store_true")
    pp.add_argument("--country", default="US")
    pp.add_argument("--law-pack", default="packs/law/us_law_pack.yaml")
    pp.add_argument("--precedents", default=None, help="precedent memory JSON")
    pp.add_argument("--ablation", default="full", choices=PipelineConfig.ABLATIONS)
    pp.set_defaults(fn=cmd_pipeline)

    r2 = sub.add_parser("rq2", help="red-team and repair loop vs R1, R1+A, R2 (scored by an independent evaluator)")
    llm_args(r2)
    r2.add_argument("--pack", action="append", default=[])
    r2.add_argument("--gold-pack", action="append", default=None)
    r2.add_argument("--planted", default="data/planted/test_seed0.json")
    r2.add_argument("--law-pack", default="packs/law/us_law_pack.yaml")
    r2.add_argument("--evaluator-backend", default="gemini-pro", help="never a backend the repair systems use")
    r2.add_argument("--evaluator-batch-queue", default=None,
                    help="store judge requests here (as q.<backend>.jsonl) instead of sending them; answer the "
                         "queue with cc batch, then rerun. Repairs still run live")
    r2.add_argument("--checker-backend", default=None)
    r2.add_argument("--attacker-backend", default=None, help="ablation: attacker on a different model")
    r2.add_argument("--systems", nargs="+", default=["loop", "r1", "r1_attacker", "r2"], choices=SYSTEMS)
    r2.add_argument("--labels", default=None)
    r2.add_argument("--allow-auto", action="store_true")
    r2.add_argument("--limit", type=int, default=None, help="e.g. 40 for the proposal's RQ2 subset")
    r2.add_argument("--max-rounds", type=int, default=3)
    r2.add_argument("--token-budget", type=int, default=None, help="same cap for every system, checker tokens included")
    r2.add_argument("--noise-floor", type=int, default=0, help="judge N unchanged (draft, rule) pairs twice")
    r2.add_argument("--no-hypotheses", action="store_true", help="skip re-checking natural loopholes")
    r2.add_argument("--acceptance-sheet", default=None, help="repairs.jsonl: write the blind acceptance sheet only")
    r2.add_argument("--sheet-out", default="runs/acceptance_sheet.csv")
    r2.add_argument("--n-sheet", type=int, default=50)
    r2.set_defaults(fn=cmd_rq2)

    k = sub.add_parser("rq2-kappa", help="blind acceptance rate per system and kappa between two raters")
    k.add_argument("sheet_a")
    k.add_argument("sheet_b")
    k.add_argument("key")
    k.set_defaults(fn=cmd_rq2_kappa)

    c = sub.add_parser("cascade", help="local-first cascade from two RQ1 runs (local, remote), simulated offline")
    c.add_argument("local")
    c.add_argument("remote")
    c.add_argument("--pack", action="append", required=True)
    c.add_argument("--gold-pack", action="append", default=None)
    c.add_argument("--law-pack", default=None)
    c.add_argument("--second-local", default=None, help="tuned-model run: escalate when the two local models disagree")
    c.add_argument("--high-severity", action="store_true", help="always escalate high-severity rules")
    c.add_argument("--cost-per-check", type=float, default=None)
    c.add_argument("--max-f1-drop", type=float, default=0.01)
    c.set_defaults(fn=cmd_cascade)

    sw = sub.add_parser("sweep", help="padded policy corpora for the policy-size sweep")
    sw.add_argument("--out", default="packs/sweep")
    sw.add_argument("--sizes", type=int, nargs="+", default=[40000, 150000])
    sw.add_argument("--padding", nargs="*", default=[], help="folders of public policy .md files")
    sw.set_defaults(fn=cmd_sweep)

    fr = sub.add_parser("frames", help="silver obligation frames for fine-tuning")
    llm_args(fr)
    fr.add_argument("action", choices=["silver"])
    fr.add_argument("--split", default="train")
    fr.add_argument("--limit", type=int, default=None)
    fr.add_argument("--out", default="data/finetune/silver_frames.jsonl")
    fr.set_defaults(fn=cmd_frames)

    ft = sub.add_parser("finetune", help="build the QLoRA training mix (train with python -m counselcopilot.finetune.train)")
    ft.add_argument("action", choices=["data"])
    ft.add_argument("--cuad", default=None, help="CUAD_v1.json")
    ft.add_argument("--frames", default=None, help="silver frames JSONL (cc frames silver)")
    ft.add_argument("--limit", type=int, default=None)
    ft.add_argument("--max-per-task", type=int, default=None)
    ft.add_argument("--out", default="data/finetune")
    ft.set_defaults(fn=cmd_finetune)

    cm = sub.add_parser("compare", help="paired bootstrap between two RQ1 runs on the same NDAs")
    cm.add_argument("run_a")
    cm.add_argument("run_b")
    cm.add_argument("--metric", default="recall", choices=["precision", "recall", "f1"])
    cm.add_argument("--score", default="strict", choices=["strict", "lenient", "rule_only"])
    cm.add_argument("--margin", type=float, default=None, help="TOST margin, e.g. 0.03 for H1")
    cm.set_defaults(fn=cmd_compare)

    rp = sub.add_parser("report", help="markdown table over RQ1 and RQ2 run folders")
    rp.add_argument("runs", nargs="+")
    rp.add_argument("--out", default=None)
    rp.set_defaults(fn=cmd_report)

    sm = sub.add_parser("smoke", help="run every experiment offline on a synthetic mini-benchmark (plumbing check)")
    sm.add_argument("--out", default="runs/smoke")
    sm.add_argument("--backend", default="heuristic")
    sm.add_argument("--judge", default="heuristic-judge")
    sm.set_defaults(fn=cmd_smoke)
