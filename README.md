# CounselCopilot

An NDA review agent built for the LMA group project (team 2025201049 · 2025201044 · 2025201068 · 2025201038).
CounselCopilot checks a consultant's NDA draft against a company's policy rules and US law, finds violations and
**omissions** with applicability-aware two-way retrieval (RQ1), and will harden the draft with a red-team and repair
loop (RQ2). The benchmark is PolicyNDA, built on ContractNLI.

| Start here | |
|---|---|
| [Proposal (PDF)](docs/proposal/proposal.pdf) | The 5-page proposal |
| [Design](docs/design/design.md) | Full design; §19 is the latest audit |
| [Latest results](docs/results/2026-10-23-claude-pilot.md) | RQ1 pilot with Claude Sonnet |
| [Docs index](docs/README.md) | Everything else: specs, reviews, course material, archive |

## Repository layout

```
src/counselcopilot/   the Python package (CLI: cc)
tests/                pytest suite
configs/              model backends and roles
packs/                policy packs (PolicyNDA companies, US law pack, clause library, toy pack)
data/                 labels and the planted benchmark (ContractNLI itself is downloaded to data/raw/)
scripts/              experiment scripts
docs/                 proposal, design, results, reviews, course material, archive
```

## Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e '.[dev]'          # add ,gemini for stage 2 and ,dense for embeddings/reranker
cc data download                 # ContractNLI (607 NDAs) into data/raw/
pytest -q                        # ~390 tests on fakes: no ContractNLI, network or GPU needed
```

## Running with a real model

**Laptop (small tests) with Ollama**

```bash
ollama pull llama3.1:8b
OLLAMA_CONTEXT_LENGTH=16384 ollama serve      # default context is too short for whole-NDA prompts
cc nli --backend llama-ollama --split dev --limit 3 --workers 2
cc review --backend llama-ollama --pack packs/toy/toy_pack.yaml --doc-id <id> --counterparty vendor
```

**Kaggle (full stage-1 runs) with vLLM**: see [docs/guides/kaggle-vllm.md](docs/guides/kaggle-vllm.md), then
`--backend llama-vllm --workers 32`.

**Gemini (stage 2)**: `pip install -e '.[gemini]'`, set `GEMINI_API_KEY`, use
`--backend gemini-flash`. Check the model id and prices in `configs/backends.toml` first.

Every LLM response is cached in `data/cache/llm.sqlite` by a hash of the full request, so
re-running a finished experiment costs nothing. `--no-cache` turns this off.
`--backend fake` runs the whole pipeline with dummy answers (plumbing check, no model).

## Commands

| Command | What it does |
|---|---|
| `cc data stats --split test` | Label counts per ContractNLI hypothesis; marks the 5 held-out ones |
| `cc nli --split dev` | Retrieves top-k spans per hypothesis and classifies them with the check primitive. Prompted-model baseline for the fine-tuning comparison, and the quickest way to test a backend |
| `cc review --pack P --doc-id N` | Reviews one NDA (or `--text file.txt`) for one deal and prints cited findings |
| `cc rq1 --pack P --split dev --preset full` | Reviews every NDA in a split and scores findings against natural gold defects (plus planted ones with `--planted`) |
| `cc compile --policies DIR --company C --gold G --out F` | Policy compiler: prose policies to requirement cards (source quote checked); with `--gold`, reports precision/recall against the gold rule list |
| `cc labels init --split test` | Writes the hand-label file pre-filled by regex (template? mutual? governing law?) for annotators to correct |
| `cc labels auto --split test` | API fallback: two models (default Qwen-72B and Mixtral-8x22B) label every NDA; a person checks only disagreements plus a 20% audit sample. `cc labels accuracy` reports audited accuracy; `rq1 --allow-auto` uses agreed labels |
| `cc labels import --split test --answers DIR_A DIR_B --pack ... --law-pack ...` | Merge two labellers' per-NDA JSON answers (e.g. Claude agents) into the label file |
| `cc packs import --company saas` | Re-check a pack written outside packgen (spec, verbatim quotes) and write REVIEW.md |
| `cc packs generate --company all` | LLM-written company policy packs: rule list first (checked against [the pack spec](docs/design/policy-pack-spec.md)), then policy prose that quotes each rule verbatim, then a second model cross-checks prose against rules. Writes `packs/policynda/<company>/` with `gold_rules.yaml`, `policies/*.md` and a `REVIEW.md` checklist |
| `cc packs check FILE...` | Checks a pack against the spec |
| `cc plant --pack P --law-pack L --split test` | Plants omissions, violations, distractors, loopholes and 30 California-law cases, re-deriving every touched label; writes a manifest with gold repairs |
| `cc retrieval --split dev [--dense M] [--rerank M]` | Gold-evidence recall@k of segment retrieval, no LLM needed |
| `cc batch submit/collect` | Gemini Batch API rounds for `rq1 --batch-queue` runs |
| `cc batch export/load` | Rounds answered by Claude agents instead of an API (`--backend claude-sonnet-agent`, also haiku and opus): export writes the queued requests as shards, agents write `{"key","text"}` answers, load puts them in the cache. `scripts/claude_pilot.sh` runs the RQ1 pilot this way; results in [docs/results](docs/results/2026-10-23-claude-pilot.md) |
| `cc rq1 --system pipeline --ablation A` | The full CounselCopilot pipeline (planner, policy/law/consistency reviewers, frames, cross-refs, verifier, approval hand-off) or one of its ablations; `--system b1/b2/b2_checklist/b3` runs the baselines |
| `cc pipeline --pack P --doc-id N` | Full pipeline on one NDA: findings, verifier verdicts, escalations and approval requests |
| `cc rq2 --pack P --planted F --limit 40` | RQ2: red-team and repair loop against R1, R1+A, R2 and the loop ablations, scored by an independent evaluator of another model family; `--acceptance-sheet` writes the blind review sheet |
| `cc rq2-kappa A.csv B.csv KEY` | Acceptance rate per system and kappa between the two blind raters |
| `cc cascade LOCAL_RUN REMOTE_RUN --pack P` | Local-first cost cascade simulated from two RQ1 runs: calibration, threshold chosen on dev, cost and F1 |
| `cc sweep --padding DIRS` | Padded policy corpora (40k, 150k tokens) for the policy-size sweep |
| `cc frames silver` / `cc finetune data` | Silver obligation frames and the QLoRA training mix ([guide](docs/guides/qlora-kaggle.md)) |
| `cc compare RUN_A RUN_B` / `cc report RUN...` | Paired bootstrap between two RQ1 runs; one Markdown table of many runs |
| `scripts/run_ablations.sh` / `cc ablations RUN...` | Every ablation study ([design](docs/design/ablation-studies.md)) on local Ollama Llama, then Gemini Flash; the report pairs each ablation with the full system (paired bootstrap, Holm-corrected) |
| `cc smoke --out runs/smoke` | Every experiment on a synthetic mini-benchmark with the offline `heuristic` backend, in about 15 s. A plumbing check, not results |

Useful `rq1` flags: `--law-pack`, `--planted`, `--labels`, `--hide-facts` (reviewer must read
personal data and governing law from the NDA), `--checker-backend` (same checker model for every
preset), `--temperature` (seed runs), `--batch-queue` (stage-synchronous batching).

`--preset` picks the RQ1 system: `full` (two-way, deal filter), `no_reverse` (forward
only, the clean RQ1 ablation), `no_filter` (no applicability filter), `reverse_only`,
`exhaustive` (B4: every rule, whole NDA), `exhaustive_filtered` (B4+filter: every applicable
rule, whole NDA; the fair competitor). Each run writes `runs/<time>-<name>/` with
`metrics.json` (P/R/F1 by defect type, false alarms per NDA, checks per NDA, tokens and $)
and per-NDA JSONL.

## Package layout

```
src/counselcopilot/
  data/contractnli.py     ContractNLI loader; held-out hypotheses (HELD_OUT_HYPOTHESES)
  data/draft.py           NDA as numbered segments; clause-level redlines (Edit) for RQ2
  policy/schema.py        Rule, PolicyPack, DealContext, LawPack; safe applicability conditions
  llm/                    one client interface: Ollama/vLLM (OpenAI-compatible), Gemini, fake;
                          SQLite response cache; token and cost accounting per agent
  retrieval/index.py      BM25 + optional dense + RRF + optional cross-encoder rerank
  review/checker.py       the check primitive (Entailment / Contradiction / NotMentioned + evidence)
  review/fields.py        field rules (governing law, term length); prompted for now
  review/policy_reviewer.py  two-way applicability-aware reviewer and its ablation presets
  benchmark/gold.py       natural gold defects from ContractNLI labels for anchored rules
  benchmark/deals.py      deterministic deal contexts per NDA
  eval/metrics.py         detection P/R/F1, false alarms, NLI metrics, bootstrap CIs
  review/deal_facts.py    reads blank deal facts (personal data, governing law) from the NDA
  benchmark/labels.py     hand-label file format and regex pre-fill
  benchmark/planter.py    defect planter with label re-derivation and gold repairs
  tools/                  tool registry (gating, arg checks, error injection), JSON agent loop,
                          legal tools, tool-calling metrics
  eval/evaluator.py       independent RQ2 evaluator + human-validation (kappa)
  llm/batch.py            Gemini Batch API submit/collect for batch mode
  review/frames.py        obligation frames (prompted, regex fallback) and frame matching
  review/xref.py          cross-reference graph between clauses
  review/law_reviewer.py, consistency.py, verifier.py   law, consistency and verifier agents
  agents/                 planner, approval desk (hand-off), precedent memory, full pipeline
  baselines/              B1 long context, B2 naive RAG (+checklist), B3 single agent
  repair/                 opposing counsel, repairer, red-team and repair loop, R1/R1+A/R2
  finetune/               QLoRA training data (NLI, CUAD, frames) and trainer
  llm/heuristic.py        offline backend for the smoke run
  benchmark/synthetic.py  synthetic mini-ContractNLI for the smoke run
  experiments/            nli, rq1, rq2, cascade, sweep and retrieval-recall runners
  commands.py             CLI commands added for the pipeline, RQ2 and the rest
packs/toy/toy_pack.yaml   TOY rules to test the code; not part of PolicyNDA
packs/law/us_law_pack.yaml      DRAFT US law pack, unchecked (needs two teammates per provision);
                                archive/ holds the old India pack
packs/law/us_law_sources.md     official text per provision, for the two checkers
packs/clauses/plant_library.yaml  clauses the planter inserts, with the hypotheses they entail
configs/backends.toml     backends, model ids, prices
```

## Choices made while building (change them if the team disagrees)

- **Held-out hypotheses:** `nda-3, nda-8, nda-12, nda-16, nda-20` (two loophole checks, the
  omission-heavy return check, two ordinary ones). Fix this before any fine-tuning run.
- **Labels mirror ContractNLI.** The check answers Entailment / Contradiction / NotMentioned
  about the rule's `term`; the rule kind (require / forbid) turns that into a violation or an
  omission. The same call is the reviewer's check, the future regression checker and the NLI
  baseline.
- **Two-way = one call per rule.** Segments found by the forward path are merged into the
  rule's reverse check, so two-way costs no more calls than reverse alone.
- **Retrieval depth k=12 plus neighbouring segments.** BM25 alone puts gold evidence in the top 8
  segments only 80% of the time on dev; k=12 with ±1 neighbour reaches 95% (`cc retrieval`).
  A clause that isn't retrieved looks absent, so this caps omission precision.
- Design fixes from the [proposal-vs-brief review](docs/reviews/proposal-vs-brief.md) are listed in the [design](docs/design/design.md) §16.

## Status (14 Nov 2026)

Every component in the proposal is built and tested (517 tests pass). See
[the final report](docs/results/final-report.md) for what maps where and what is left. Still to
do, all by people or with real models:

1. Human review: each pack's `packs/policynda/<company>/REVIEW.md`, the 55 disputed keys in
   `data/labels/ndas_auto.yaml`, and two teammates per provision of the law pack.
2. Real runs: RQ1 (Llama, then Gemini Flash), the policy-size sweep, RQ2 on 40 NDAs, the cascade,
   two QLoRA seeds, and the blind acceptance review.
3. Decide the H1 wording ("fewer tokens" instead of "fewer checks", see the
   [pilot](docs/results/2026-10-23-claude-pilot.md)) and send the TA the change note.
