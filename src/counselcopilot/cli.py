"""Command line: `cc <command> --help` for options.

    cc data download                       fetch ContractNLI into data/raw/
    cc data stats --split test             label counts per hypothesis
    cc nli --backend llama-ollama --split dev --limit 5
    cc review --backend llama-ollama --pack packs/toy/toy_pack.yaml --doc-id 1 --counterparty vendor
    cc rq1 --backend llama-ollama --pack packs/toy/toy_pack.yaml --split dev --preset full --limit 5
    cc labels init --split test                      pre-fill hand labels for annotators
    cc labels auto --split test                      two-model labels; a person checks disagreements
    cc packs generate --company all                  LLM-written policy packs (rules first, then prose)
    cc packs check packs/policynda/*/gold_rules.yaml check a pack against docs/design/policy-pack-spec.md
    cc plant --pack packs/toy/toy_pack.yaml --law-pack packs/law/us_law_pack.yaml --split test
    cc retrieval --split dev [--dense BAAI/bge-small-en-v1.5]
    cc batch submit|collect ...                      Gemini Batch API rounds
    cc batch export|load ...                         rounds answered by Claude agents
"""

from __future__ import annotations

import argparse
import json
import sys

DEFAULT_DATA = "data/raw"
PRESETS = ["full", "no_reverse", "no_filter", "reverse_only", "exhaustive", "exhaustive_filtered"]


def _load_data(args, splits=("train", "dev", "test")):
    from .data.contractnli import load_contractnli

    return load_contractnli(args.data, splits)


def cmd_data(args) -> None:
    if args.action == "download":
        from .data.download import download_contractnli

        print(f"ContractNLI ready in {download_contractnli(args.data)}")
        return
    data = _load_data(args, (args.split,))
    counts = data.label_counts(args.split)
    print(f"{args.split}: {len(data[args.split])} NDAs")
    print(f"{'hypothesis':<8} {'held':<5} {'description':<48} {'E':>4} {'C':>4} {'N':>4}")
    for h in data.hypothesis_keys:
        c = counts[h]
        print(f"{h:<8} {'yes' if data.hypotheses[h].held_out else '':<5} "
              f"{data.hypotheses[h].short_description[:48]:<48} "
              f"{c['Entailment']:>4} {c['Contradiction']:>4} {c['NotMentioned']:>4}")


def cmd_nli(args) -> None:
    from .experiments.nli import run_nli
    from .llm import load_backend

    llm = load_backend(args.backend, args.config, use_cache=not args.no_cache)
    m = run_nli(llm, _load_data(args, (args.split,)), args.split, args.hypotheses, args.limit,
                args.k, args.whole_doc, args.workers)
    print(json.dumps({k: m[k] for k in ("all", "errors", "usage", "out_dir")}, indent=1))


def cmd_review(args) -> None:
    from .data.draft import Draft
    from .llm import load_backend
    from .policy.schema import DealContext, PolicyPack
    from .review.policy_reviewer import PolicyReviewer, ReviewConfig

    llm = load_backend(args.backend, args.config, use_cache=not args.no_cache)
    pack = PolicyPack.load(args.pack)
    if args.text:
        draft = Draft.from_text(open(args.text, encoding="utf-8").read(), args.text)
    else:
        draft = Draft.from_nda(_load_data(args).by_id(args.doc_id))
    deal = DealContext(company=pack.company, counterparty_type=args.counterparty,
                       personal_data=True if args.personal_data else None, counterparty_country=args.country)
    cfg = ReviewConfig.preset(args.preset)
    cfg.max_workers = args.workers
    res = PolicyReviewer(llm, pack, cfg, law_pack=_law_pack(args.law_pack)).review(draft, deal)
    print(f"Deal (after reading the NDA): {res.deal.model_dump(mode='json')}")
    print(f"Applicable rules: {', '.join(res.applicable_rules)}  ({res.n_checks} checks)\n")
    for f in res.findings:
        print(f"- {f.type.value.upper():<16} {f.rule_id:<8} conf={f.confidence:.2f}  {f.explanation}")
        for i in f.evidence:
            print(f"      [{i}] {draft.segments[i][:160]}")
    if not res.findings:
        print("No findings.")
    print(f"\nTokens: {llm.total_usage()}")


def _law_pack(path):
    if not path:
        return None
    from .policy.schema import LawPack

    lp = LawPack.load(path)
    if lp.unchecked():
        print(f"WARNING: law pack provisions not yet checked by two teammates: {', '.join(lp.unchecked())}",
              file=sys.stderr)
    return lp


def cmd_rq1(args) -> None:
    from .benchmark.deals import load_deals
    from .benchmark.planter import load_planted
    from .experiments.rq1 import run_rq1
    from .llm import load_backend
    from .policy.schema import PolicyPack

    llm = load_backend(args.backend, args.config, use_cache=not args.no_cache, batch_queue=args.batch_queue)
    checker = (load_backend(args.checker_backend, args.config, use_cache=not args.no_cache,
                            batch_queue=args.batch_queue) if args.checker_backend else None)
    packs = [PolicyPack.load(p) for p in args.pack]
    deals = load_deals(args.deals) if args.deals else None
    m = run_rq1(llm, _load_data(args, (args.split,)), packs, args.split, args.preset, args.limit,
                deals, args.labels, args.seed, max_workers=args.workers, law_pack=_law_pack(args.law_pack),
                planted=load_planted(args.planted) if args.planted else None, checker_llm=checker,
                temperature=args.temperature, hide_facts=args.hide_facts,
                allow_unverified_labels=args.allow_unverified, allow_auto_labels=args.allow_auto)
    keys = ("strict", "checks_per_nda", "applicable_rules_per_nda", "fact_accuracy", "pending_batch_ndas",
            "usage", "out_dir")
    print(json.dumps({k: m[k] for k in keys}, indent=1, default=str))
    if m["pending_batch_ndas"]:
        print(f"{m['pending_batch_ndas']} NDAs waiting on the batch queue {args.batch_queue}; "
              "submit it, collect the results, and run this command again.", file=sys.stderr)


def cmd_labels(args) -> None:
    from .benchmark.labels import load_labels, write_prefilled

    if args.action == "accuracy":
        from .benchmark.autolabel import label_accuracy

        print(json.dumps(label_accuracy(load_labels(args.out, allow_unverified=True)), indent=1))
        return
    if args.action == "import-counterparty":  # add counterparty kind/role/country to an existing label file
        from pathlib import Path

        import yaml

        from .benchmark.autolabel import add_counterparty_labels

        ans = [{int(f.stem): json.loads(f.read_text()) for f in Path(d).glob("*.json") if f.stem.isdigit()}
               for d in args.answers]
        labels = load_labels(args.out, allow_unverified=True)
        stats = add_counterparty_labels(labels, ans[0], ans[1], tuple(args.names))
        Path(args.out).write_text(yaml.safe_dump(labels, sort_keys=True, allow_unicode=True))
        print(json.dumps(stats, indent=1))
        return
    docs = _load_data(args, (args.split,))[args.split][: args.limit]
    if args.action == "init":
        n = write_prefilled(docs, args.out)
        print(f"wrote {n} pre-filled entries to {args.out}; annotators correct them and set verified: true")
        return
    from .benchmark.autolabel import autolabel, rule_terms, write_autolabels
    from .experiments.common import usage_report
    from .llm import load_backend
    from .policy.schema import PolicyPack

    law = _law_pack(args.law_pack)
    terms = rule_terms(law.as_rules()) if law else {}
    for path in args.pack or []:
        pk = PolicyPack.load(path)
        terms.update(rule_terms(pk.rules, pk.company))

    if args.action == "import":
        from pathlib import Path

        from .benchmark.autolabel import autolabel_from_answers

        ans = [{int(f.stem): json.loads(f.read_text()) for f in Path(d).glob("*.json") if f.stem.isdigit()}
               for d in args.answers]
        labels = autolabel_from_answers(docs, ans[0], ans[1], tuple(args.names), args.audit_share, args.seed, terms)
        stats = write_autolabels(labels, args.out)
        missing = sorted(d.id for d in docs if d.id not in labels)
        print(json.dumps({**stats, "missing_answers": missing}, indent=1))
        return
    from .llm.factory import family

    if family(args.backend_a, args.config) == family(args.backend_b, args.config) != "fake":
        sys.exit("the two labelling backends must be different model families, or they share their mistakes")
    a = load_backend(args.backend_a, args.config, use_cache=not args.no_cache)
    b = load_backend(args.backend_b, args.config, use_cache=not args.no_cache)
    stats = write_autolabels(autolabel(docs, a, b, (args.backend_a, args.backend_b), args.workers,
                                       args.audit_share, args.seed, terms), args.out)
    print(json.dumps({**stats, "usage": {args.backend_a: usage_report(a), args.backend_b: usage_report(b)}},
                     indent=1, default=str))
    print(f"a person checks the {stats['need_person']} entries with auto.needs_person: true, sets verified: true, "
          "and lists any keys they changed under auto.corrected", file=sys.stderr)


def cmd_packs(args) -> None:
    from .policy.schema import PolicyPack

    if args.action == "check":
        from .benchmark.packgen import check_spec

        hyps = set(_load_data(args, ("test",)).hypotheses) if args.data_check else None
        for path in args.path:
            problems = check_spec(PolicyPack.load(path), hyps)
            print(f"{path}: " + ("meets the spec" if not problems else "\n  - " + "\n  - ".join(problems)))
        return
    if args.action == "import":
        from pathlib import Path

        from .benchmark.packgen import PROFILES, import_pack

        hyps = {k: h.text for k, h in _load_data(args, ("test",)).hypotheses.items()}
        flagged = json.loads(Path(args.flagged).read_text()) if args.flagged else None
        for slug in (list(PROFILES) if args.company == "all" else [args.company]):
            g = import_pack(Path(args.out) / slug, PROFILES[slug], hyps, args.generator_name,
                            "claude-haiku (agent)" if flagged is not None else None, flagged)
            print(f"{slug}: {len(g.pack.rules)} rules, {g.n_words:,} words; {len(g.spec_problems)} spec problems, "
                  f"{len(g.quote_problems)} quote problems -> {Path(args.out) / slug / 'REVIEW.md'}")
            for x in g.spec_problems + g.quote_problems:
                print("  -", x)
        return
    from .benchmark.packgen import PROFILES, PackGenerator, save_generated
    from .experiments.common import usage_report
    from .llm import load_backend

    from .llm.factory import check_data_maker

    clash = check_data_maker([args.backend], args.config)
    if clash and not args.allow_same_family:
        sys.exit("refusing: " + "; ".join(clash) + " (--allow-same-family for pilots)")
    data = _load_data(args, ("test",))
    counts = data.label_counts("test")
    natural = [h for h in data.hypothesis_keys if counts[h]["Contradiction"] > 0]
    llm = load_backend(args.backend, args.config, use_cache=not args.no_cache)
    checker = load_backend(args.checker_backend, args.config, use_cache=not args.no_cache) if args.checker_backend else None
    gen = PackGenerator(llm, checker, {k: h.text for k, h in data.hypotheses.items()}, natural,
                        PolicyPack.load(args.example_pack), target_words=args.words, seed=args.seed)
    for slug in (list(PROFILES) if args.company == "all" else [args.company]):
        g = gen.generate(PROFILES[slug], workers=args.workers)
        out = save_generated(g, args.out, args.backend, args.checker_backend)
        print(f"{slug}: {len(g.pack.rules)} rules, {len(g.documents)} documents, {g.n_words:,} words; "
              f"{len(g.spec_problems)} spec problems, {len(g.quote_problems)} missing quotes, "
              f"{len(g.flagged)} rules flagged by the cross-check -> {out}/REVIEW.md")
    print(json.dumps({"usage": usage_report(llm), "checker_usage": usage_report(checker) if checker else None},
                     indent=1, default=str))


def cmd_plant(args) -> None:
    from .benchmark.deals import generate_deals, load_deals, save_deals
    from .benchmark.labels import load_labels
    from .benchmark.planter import Planter, plant_split, save_planted
    from .policy.schema import PolicyPack

    data = _load_data(args, (args.split,))
    docs = data[args.split]
    packs = [PolicyPack.load(p) for p in args.pack]
    law = _law_pack(args.law_pack)
    labels = load_labels(args.labels, args.allow_unverified, args.allow_auto)  # same policy as rq1
    deals = load_deals(args.deals) if args.deals else generate_deals(
        [d.id for d in docs], [p.company for p in packs], args.seed, labels=labels)
    planters = {p.company: Planter(p, law) for p in packs}
    planted = plant_split(planters, docs, deals, labels, args.seed,
                          n_state_law=args.n_state_law, state=args.state)
    save_planted(planted, args.out)
    save_deals(deals, args.out.replace(".json", "_deals.json"))
    n_def = sum(len(p.defects) for p in planted)
    print(f"planted {n_def} defects in {len(planted)} NDAs "
          f"({sum(not p.defects for p in planted)} with no planted defect, "
          f"{sum(any('distractor' in x for x in p.log) for p in planted)} with a distractor, "
          f"{sum(any(lh.get('origin') == 'planted' for lh in p.loopholes) for p in planted)} with a planted loophole, "
          f"{sum(bool(p.injection) for p in planted)} with injection text, "
          f"{sum(p.field_overrides.get('governing_law') == args.state.lower() for p in planted)} "
          f"switched to {args.state} law) -> {args.out}")


def cmd_retrieval(args) -> None:
    from .experiments.retrieval_recall import retrieval_recall

    print(json.dumps(retrieval_recall(_load_data(args, (args.split,)), args.split, dense=args.dense,
                                      rerank=args.rerank, neighbours=args.neighbours), indent=1))


def cmd_batch(args) -> None:
    from .llm import ResponseCache
    from .llm import batch as gb
    from .llm.factory import backend_config

    b = backend_config(args.backend, args.config)
    # queues are per backend: rq1 --batch-queue q.jsonl writes q.<backend>.jsonl for each model
    if args.action in ("submit", "export", "load") and f".{args.backend}." not in str(args.queue):
        raise SystemExit(f"{args.queue} is not the queue for {args.backend}; submit q.{args.backend}.jsonl with "
                         f"--backend {args.backend}")
    cache = ResponseCache(b["cache_path"])
    if args.action == "export":
        print(json.dumps(gb.export_shards(args.queue, args.out, cache, args.per_shard), indent=1))
        return
    if args.action == "load":
        print(gb.load_answers(args.answers, args.queue, b["model"], cache))
        return
    if args.action == "submit":
        print(gb.submit(args.queue, b["model"], b.get("thinking_budget")))
    else:
        print(gb.collect(args.job, b["model"], cache))


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(prog="cc", description="CounselCopilot")
    p.add_argument("--data", default=DEFAULT_DATA, help="folder with ContractNLI json files")
    p.add_argument("--config", default=None, help="backends TOML (default configs/backends.toml)")
    sub = p.add_subparsers(dest="cmd", required=True)

    d = sub.add_parser("data")
    d.add_argument("action", choices=["download", "stats"])
    d.add_argument("--split", default="test")
    d.set_defaults(fn=cmd_data)

    def llm_args(sp):
        sp.add_argument("--backend", default="llama-ollama")
        sp.add_argument("--no-cache", action="store_true")
        sp.add_argument("--workers", type=int, default=8)

    n = sub.add_parser("nli", help="ContractNLI with the check primitive")
    llm_args(n)
    n.add_argument("--split", default="dev")
    n.add_argument("--hypotheses", default="all", help="all | held_out | train | nda-1,nda-16,...")
    n.add_argument("--limit", type=int, default=None, help="first N documents only")
    n.add_argument("--k", type=int, default=12, help="spans retrieved per hypothesis")
    n.add_argument("--whole-doc", action="store_true", help="show the whole NDA instead of top-k")
    n.set_defaults(fn=cmd_nli)

    r = sub.add_parser("review", help="review one NDA against one policy pack")
    llm_args(r)
    r.add_argument("--pack", required=True)
    g = r.add_mutually_exclusive_group(required=True)
    g.add_argument("--doc-id", type=int)
    g.add_argument("--text", help="plain-text NDA file")
    r.add_argument("--counterparty", default="vendor", choices=["vendor", "customer", "employee", "partner"])
    r.add_argument("--personal-data", action="store_true")
    r.add_argument("--country", default="US")
    r.add_argument("--law-pack", default=None)
    r.add_argument("--preset", default="full", choices=PRESETS)
    r.set_defaults(fn=cmd_review)

    q = sub.add_parser("rq1", help="score a system configuration on benchmark NDAs")
    llm_args(q)
    q.add_argument("--pack", action="append", required=True, help="repeat for several companies")
    q.add_argument("--split", default="dev")
    q.add_argument("--preset", default="full", choices=PRESETS)
    q.add_argument("--limit", type=int, default=None)
    q.add_argument("--deals", default=None, help="deal-context JSON; generated from --seed if omitted")
    q.add_argument("--labels", default=None, help="hand labels YAML (cc labels init)")
    q.add_argument("--allow-unverified", action="store_true", help="also use labels not marked verified")
    q.add_argument("--allow-auto", action="store_true",
                   help="also use auto labels both models agreed on (cc labels auto)")
    q.add_argument("--law-pack", default=None)
    q.add_argument("--planted", default=None, help="planter manifest (cc plant); reviews the planted drafts")
    q.add_argument("--checker-backend", default=None,
                   help="model for every rule check, same for all presets (e.g. the QLoRA model)")
    q.add_argument("--temperature", type=float, default=0.0, help=">0 for seed runs")
    q.add_argument("--hide-facts", action="store_true",
                   help="leave personal data and governing law blank; the reviewer reads them from the NDA")
    q.add_argument("--batch-queue", default=None, help="batch mode: queue uncached requests here")
    q.add_argument("--seed", type=int, default=0)
    q.set_defaults(fn=cmd_rq1)

    lb = sub.add_parser("labels", help="hand-label file for annotators")
    lb.add_argument("action", choices=["init", "auto", "accuracy", "import", "import-counterparty"],
                    help="init: regex pre-fill; auto: two-model labels; accuracy: audited auto-label accuracy")
    lb.add_argument("--split", default="test")
    lb.add_argument("--limit", type=int, default=None)
    lb.add_argument("--out", default="data/labels/ndas.yaml")
    lb.add_argument("--backend-a", default="qwen-hosted")
    lb.add_argument("--backend-b", default="gemini-pro", help="must be a different model family from --backend-a")
    lb.add_argument("--pack", nargs="*", default=[], help="auto: label presence of these packs' unanchored rule terms")
    lb.add_argument("--law-pack", default=None, help="auto: also label presence of law-pack terms")
    lb.add_argument("--answers", nargs=2, default=None, metavar=("DIR_A", "DIR_B"),
                    help="import: folders of <doc_id>.json answers written by two labellers (e.g. Claude agents)")
    lb.add_argument("--names", nargs=2, default=["claude-sonnet", "claude-haiku"], help="import: labeller names")
    lb.add_argument("--audit-share", type=float, default=0.2, help="share of agreed entries a person checks")
    lb.add_argument("--seed", type=int, default=0)
    lb.add_argument("--no-cache", action="store_true")
    lb.add_argument("--workers", type=int, default=4)
    lb.set_defaults(fn=cmd_labels)

    pk = sub.add_parser("packs", help="generate or check PolicyNDA company policy packs")
    pk.add_argument("action", choices=["generate", "check", "import"],
                    help="import: re-check a pack written outside packgen (e.g. by a Claude agent) and write REVIEW.md")
    pk.add_argument("path", nargs="*", help="check: gold_rules.yaml files")
    pk.add_argument("--company", default="all", choices=["all", "saas", "hospital", "manufacturer"])
    pk.add_argument("--backend", default="qwen-hosted",
                    help="generator; must be a model family no backbone, compiler or evaluator uses ([roles])")
    pk.add_argument("--checker-backend", default="gemini-pro", help="cross-checks prose against rules")
    pk.add_argument("--generator-name", default="claude-sonnet (agent)", help="import: who wrote the pack")
    pk.add_argument("--flagged", default=None, help="import: JSON rule id -> problem from a cross-check")
    pk.add_argument("--allow-same-family", action="store_true", help="skip the family check (pilots only)")
    pk.add_argument("--example-pack", default="packs/toy/toy_pack.yaml")
    pk.add_argument("--words", type=int, default=30000, help="prose words per pack (~40k tokens)")
    pk.add_argument("--out", default="packs/policynda")
    pk.add_argument("--data-check", action="store_true", help="check: also check anchors against ContractNLI")
    pk.add_argument("--seed", type=int, default=0)
    pk.add_argument("--no-cache", action="store_true")
    pk.add_argument("--workers", type=int, default=4)
    pk.set_defaults(fn=cmd_packs)

    pl = sub.add_parser("plant", help="plant defects, distractors, loopholes and state-law cases")
    pl.add_argument("--pack", action="append", required=True)
    pl.add_argument("--law-pack", default=None)
    pl.add_argument("--split", default="test")
    pl.add_argument("--labels", default=None)
    pl.add_argument("--allow-unverified", action="store_true", help="also use labels not marked verified")
    pl.add_argument("--allow-auto", action="store_true", help="also use auto labels both models agreed on")
    pl.add_argument("--deals", default=None)
    pl.add_argument("--n-state-law", type=int, default=30, help="NDAs switched to --state governing law")
    pl.add_argument("--state", default="California")
    pl.add_argument("--seed", type=int, default=0)
    pl.add_argument("--out", default="data/planted/test.json")
    pl.set_defaults(fn=cmd_plant)

    rt = sub.add_parser("retrieval", help="gold-evidence recall@k of segment retrieval (no LLM)")
    rt.add_argument("--split", default="dev")
    rt.add_argument("--dense", default=None, help="sentence-transformers model, e.g. BAAI/bge-small-en-v1.5")
    rt.add_argument("--rerank", default=None, help="cross-encoder, e.g. BAAI/bge-reranker-base")
    rt.add_argument("--neighbours", type=int, default=0)
    rt.set_defaults(fn=cmd_retrieval)

    bt = sub.add_parser("batch", help="batch rounds for --batch-queue runs: Gemini Batch API or Claude agents")
    bt.add_argument("action", choices=["submit", "collect", "export", "load"],
                    help="submit/collect: Gemini Batch API; export/load: shards answered by Claude agents")
    bt.add_argument("--backend", default="gemini-flash")
    bt.add_argument("--queue", default="runs/queue.jsonl")
    bt.add_argument("--job", default=None)
    bt.add_argument("--out", default="runs/agent_round", help="export: folder for the shards")
    bt.add_argument("--per-shard", type=int, default=60, help="export: requests per shard")
    bt.add_argument("--answers", default=None, help="load: folder of agents' answer .jsonl files")
    bt.set_defaults(fn=cmd_batch)

    args = p.parse_args(argv)
    args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
