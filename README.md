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
pytest -q                        # 39 tests, no network or GPU needed
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
| `cc labels init --split test` | Writes the hand-label file pre-filled by regex (template? mutual? governing law?) for annotators to correct |
| `cc labels auto --split test` | API fallback: two models (default Qwen-72B and Gemini Pro) label every NDA; a person checks only disagreements plus a 20% audit sample. `cc labels accuracy` reports audited accuracy; `rq1 --allow-auto` uses agreed labels |
| `cc labels import --split test --answers DIR_A DIR_B --pack ... --law-pack ...` | Merge two labellers' per-NDA JSON answers (e.g. Claude agents) into the label file |
| `cc packs import --company saas` | Re-check a pack written outside packgen (spec, verbatim quotes) and write REVIEW.md |
| `cc packs generate --company all` | LLM-written company policy packs: rule list first (checked against [the pack spec](docs/design/policy-pack-spec.md)), then policy prose that quotes each rule verbatim, then a second model cross-checks prose against rules. Writes `packs/policynda/<company>/` with `gold_rules.yaml`, `policies/*.md` and a `REVIEW.md` checklist |
| `cc packs check FILE...` | Checks a pack against the spec |
| `cc plant --pack P --law-pack L --split test` | Plants omissions, violations, distractors, loopholes and 30 California-law cases, re-deriving every touched label; writes a manifest with gold repairs |
| `cc retrieval --split dev [--dense M] [--rerank M]` | Gold-evidence recall@k of segment retrieval, no LLM needed |
| `cc batch submit/collect` | Gemini Batch API rounds for `rq1 --batch-queue` runs |
| `cc batch export/load` | Rounds answered by Claude agents instead of an API (`--backend claude-sonnet-agent`, also haiku and opus): export writes the queued requests as shards, agents write `{"key","text"}` answers, load puts them in the cache. `scripts/claude_pilot.sh` runs the RQ1 pilot this way; results in [docs/results](docs/results/2026-10-23-claude-pilot.md) |

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
  experiments/            nli, rq1 and retrieval-recall runners
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

## Not built yet (next steps, in design order)

1. Human review: each pack's `packs/policynda/<company>/REVIEW.md`, the disputed keys and audit sample in
   `data/labels/ndas_auto.yaml` (packs and labels were written by Claude agents, 23 Oct 2026); law-pack check (team).
2. Consistency reviewer tools; planner; verifier; approval agent on the tool registry; precedent memory.
3. Baselines B1 (long context, Gemini only), B2 (naive RAG over policy prose), B3 (single agent).
4. Policy compiler (prose -> rule base, Gemini Pro once).
5. RQ2: opposing-counsel agent, repairer, regression checker, R1, R1+A and R2 baselines (the independent evaluator is built).
6. Obligation-frame matching, the cross-reference graph, the CUAD clause library and the local-first cascade.
7. Wire the JSON tool-calling agent (`tools/agent.py`) into the reviewers, so tool-use metrics come from real runs.
8. QLoRA multi-task fine-tune (CUAD tags, ContractNLI on 12 hypotheses, obligation frames).
