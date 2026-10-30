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
pytest -q                        # ~390 tests on fakes: no ContractNLI, network or GPU needed; on Windows set PYTHONUTF8=1 first
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
| `cc compare --pack P --doc-id N --presets full agentic` | Reviews one NDA (or `--text file.txt`) under each preset and prints which rules' findings differ, with checks, model calls and tokens per preset. For a quick look; scored comparisons come from one `cc rq1` run per preset |
| `cc labels init --split test` | Writes the hand-label file pre-filled by regex (template? mutual? governing law?) for annotators to correct |
| `cc labels auto --split test` | API fallback: two models (default Qwen-72B and Gemini Pro) label every NDA; a person checks only disagreements plus a 20% audit sample. `cc labels accuracy` reports audited accuracy; `rq1 --allow-auto` uses agreed labels |
| `cc labels import --split test --answers DIR_A DIR_B --pack ... --law-pack ...` | Merge two labellers' per-NDA JSON answers (e.g. Claude agents) into the label file |
| `cc packs import --company saas` | Re-check a pack written outside packgen (spec, verbatim quotes) and write REVIEW.md |
| `cc packs generate --company all` | LLM-written company policy packs: rule list first (checked against [the pack spec](docs/design/policy-pack-spec.md)), then policy prose that quotes each rule verbatim, then a second model cross-checks prose against rules. Writes `packs/policynda/<company>/` with `gold_rules.yaml`, `policies/*.md` and a `REVIEW.md` checklist |
| `cc packs check FILE...` | Checks a pack against the spec |
| `cc plant --pack P --law-pack L --split test` | Plants omissions, violations, distractors, loopholes and 30 California-law cases, re-deriving every touched label; writes a manifest with gold repairs |
| `cc db seed` / `cc db status` | Copies the three company packs, the US law pack and their documents into Postgres (needs `pip install -e '.[db]'` and `DATABASE_URL`; see `.env.example`), or lists what the database holds and whether each pack still matches its YAML. Then any command takes `--pack pg:saas` (also `pg:hospital`, `pg:manufacturer`) and `--law-pack pg:us-law`. The YAML stays the reviewed source: `seed` overwrites the database's copy |
| `cc retrieval --split dev [--dense M] [--rerank M]` | Gold-evidence recall@k of segment retrieval, no LLM needed |
| `cc web-search "topic" [--source us_code\|cfr\|federal_register]` | Live search of official US legal sources, also available to agents as the `web_search` tool in `tools/legal_tools.py`. For people checking the law pack: results are unreviewed leads, and the law pack only changes by hand. Never search for NDA text, because queries leave the machine; the reviewer's agents do not have this tool. California law is not covered. Describe the rule in plain words: on `us_code`, quoted phrases return nothing and short queries miss sections. `us_code` uses GovInfo's shared demo key (about 10 calls an hour) unless `GOVINFO_API_KEY` is set, in the environment or in `.env` |
| `cc law-check [--law-pack pg:us-law]` | Reads each provision's official `source_url`, shows how many of its summary's words are on the page, adds search leads for federal provisions, and saves a report for the two people signing off the pack to `runs/`. A reading aid only: it changes nothing in the pack. California's site refuses automated readers, so those three provisions are listed to open in a browser |
| `cc batch submit/collect` | Gemini Batch API rounds for `rq1 --batch-queue` runs |
| `cc batch export/load` | Rounds answered by Claude agents instead of an API (`--backend claude-sonnet-agent`, also haiku and opus): export writes the queued requests as shards, agents write `{"key","text"}` answers, load puts them in the cache. `scripts/claude_pilot.sh` runs the RQ1 pilot this way; results in [docs/results](docs/results/2026-10-23-claude-pilot.md) |

**Local Postgres on Windows.** Smart App Control blocks the Windows `initdb.exe`, so the database
runs in WSL Ubuntu, under `~/.counselcopilot`, on `127.0.0.1:5433` (only this PC can reach it). The
URL is in `.env`. It does not start by itself after a reboot; from PowerShell:

```powershell
$root = "/home/tanooj/.counselcopilot"
wsl -d Ubuntu --exec "$root/pg/bin/pg_ctl" -D "$root/pgdata" -l "$root/postgres.log" -w start
```

To run the database tests as well, set `CC_TEST_DATABASE_URL` to the same URL; they use a throwaway
schema and leave the packs alone.

Useful `rq1` flags: `--law-pack`, `--planted`, `--labels`, `--hide-facts` (reviewer must read
personal data and governing law from the NDA), `--checker-backend` (same checker model for every
preset), `--temperature` (seed runs), `--batch-queue` (stage-synchronous batching).

`--preset` picks the RQ1 system: `full` (two-way, deal filter), `agentic` (`full`, plus an
agent that searches the NDA again whenever a reverse check says NotMentioned or has confidence
under 0.7; the same checker then decides on the wider evidence, and the search shows up in
`usage.by_agent` as `agentic_search` and `agentic_check`. With `--batch-queue` each agent step
is one more batch round), `no_reverse` (forward
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
  policy/store.py         the packs in Postgres (`pg:<slug>`), seeded from the YAML
  llm/                    one client interface: Ollama/vLLM (OpenAI-compatible), Gemini, fake;
                          SQLite response cache; token and cost accounting per agent
  retrieval/index.py      BM25 + optional dense + RRF + optional cross-encoder rerank
  review/checker.py       the check primitive (Entailment / Contradiction / NotMentioned + evidence)
  review/fields.py        field rules (governing law, term length); prompted for now
  review/policy_reviewer.py  two-way applicability-aware reviewer and its ablation presets
  review/agentic.py       agentic second-look evidence search (read-only tools; never judges)
  benchmark/gold.py       natural gold defects from ContractNLI labels for anchored rules
  benchmark/deals.py      deterministic deal contexts per NDA
  eval/metrics.py         detection P/R/F1, false alarms, NLI metrics, bootstrap CIs
  review/deal_facts.py    reads blank deal facts (personal data, governing law) from the NDA
  benchmark/labels.py     hand-label file format and regex pre-fill
  benchmark/planter.py    defect planter with label re-derivation and gold repairs
  tools/                  tool registry (gating, arg checks, error injection), JSON agent loop,
                          legal tools, web search of official US sources, tool-calling metrics
  eval/evaluator.py       independent RQ2 evaluator + human-validation (kappa)
  llm/batch.py            Gemini Batch API submit/collect for batch mode
  experiments/            nli, rq1, retrieval-recall, one-NDA compare and law-check runners
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
