# Ollama run: agentic RAG and tool calling after merging `tanooj` and `guru` (15 Nov 2026)

First run of the merged code on a local model. `tanooj` added the agentic RAG preset (`--preset agentic`: when a reverse
check comes back NotMentioned or under 0.7 confidence, an agent searches the NDA again and re-checks). `guru` added the
tool-calling evaluation (`cc tools`).

**Setup.** `llama3.1:8b` (Q4) on Ollama 0.40.16, backend `llama-ollama`, laptop RTX 3050 6 GB (23 of 33 layers on the
GPU), `OLLAMA_CONTEXT_LENGTH=16384`, flash attention, q8_0 KV cache, temperature 0, one worker.

- **RQ1:** the first 5 planted test NDAs (`data/planted/test_seed0.json`), the three PolicyNDA gold packs plus the US
  law pack, auto labels (`--allow-auto`), deal facts hidden (`--hide-facts`). These are oracle-rules runs: the reviewer
  gets the gold rules directly, with no `cc compile` step, the same as `ORACLE=1 scripts/claude_pilot.sh`.
- **Tools:** `cc tools` with the saas gold pack and the US law pack, the first 10 episodes (5 of them carry injection
  text), max 8 steps, once at tool error rate 0 and once at 0.1 (the design value).

## RQ1: `full` against `agentic`

Strict scoring: rule, type and cited evidence must all match. There are 53 gold defects.

| Preset | Precision | Recall | F1 (95% CI) | Omission P / R | Violation P / R | Checks per NDA | Agent searches per NDA | Model calls | Prompt tokens | Wall time |
|---|---|---|---|---|---|---|---|---|---|---|
| `full` | 0.46 | 0.45 | 0.46 (0.35–0.56) | 0.64 / 0.40 | 0.14 / 0.33 | 24.4 | – | 111 | 117k | 7.7 min |
| `agentic` | 0.43 | 0.42 | 0.42 (0.34–0.51) | 0.71 / 0.34 | 0.12 / 0.33 | 29.2 | 7.2 | 279 | 261k | 11.8 min |

Approval-needed findings (P/R 0.83/0.83) and statutory-risk findings (0.67/0.67) score the same under both presets. Deal
facts read from the NDA: governing law 5/5, personal data 2/3.

**What it shows**

1. **Agentic search did not help this model.** It ran 7.2 extra searches per NDA and spent 2.2 times the prompt tokens.
   Omission precision rose (0.64 to 0.71), but omission recall fell (0.40 to 0.34): the wider second check talked the
   model out of a few true omissions. Overall F1 went from 0.46 to 0.42.
2. **The difference is inside the noise.** The confidence intervals overlap almost completely (0.35–0.56 against
   0.34–0.51), and only 2 of the 5 NDAs scored differently.
3. **Violations are the weak spot, as in the Claude pilot.** Precision is 0.12–0.14: most false alarms are violations.
4. **llama3.1:8b sits well below the Claude Sonnet pilot.** The pilot reached strict F1 0.76 on 20 NDAs with `full`.
   Read these numbers as a plumbing and relative check, not as the project's results.

### Follow-up: what the agent's searches actually changed, and a gate on the re-check

In the run above the agent searched 36 times. 12 searches found no new segments, so no re-check ran. 15 re-checks
returned the same label. 9 changed the first check's NotMentioned:

| Change | Gold | Count | Effect |
|---|---|---|---|
| NotMentioned → Entailment | no defect | 5 | fixed a false omission alarm |
| NotMentioned → Contradiction | no defect | 2 | added a false violation |
| NotMentioned → Entailment | omission | 2 | lost a true omission |

**None of the 9 changes came from what the search found.** Every segment the re-checks cited (10 in total) had
already been shown to the first check. The agent's new segments were never cited. The model changed its mind about the
same text because the prompt was longer, and 5 of 9 times that happened to be right. The first check already sees
22–37 of an NDA's ~71 segments (12 hits plus ±1 neighbours), so there is little left for a search to find.

**Fix** (`ReviewConfig.agentic_switch_confidence`, `PolicyReviewer._accept_second`). The re-check may replace the first
check's label only if it cites a segment the search added, with confidence at least 0.8 and at least the first check's.
A first check that saw no segments counts as a non-judgement, so its 1.0 confidence is not used as a floor. A re-check
that keeps the label is always accepted. Each re-check's decision is logged as `accepted` in `reviews.jsonl`.

| Preset | Precision | Recall | F1 | Label changes accepted | Model calls |
|---|---|---|---|---|---|
| `full` | 0.46 | 0.45 | 0.46 | – | 111 |
| `agentic`, re-check always trusted (before) | 0.43 | 0.42 | 0.42 | 9 / 9 | 279 |
| `agentic` with the gate (after) | 0.46 | 0.45 | 0.46 | 0 / 9 | 279 (all cached) |

The gate removes the harm: `agentic` no longer loses true omissions or adds false violations. It cannot create a gain,
because with this model and this data the search never surfaced evidence that mattered. Agentic RAG now costs 2.5 times
the calls for the same result. It can only pay off where the first retrieval misses real evidence: a stronger checker,
longer documents, or the policy corpus (~40k tokens per company, more than the 16k context), which the preset does not
search yet. The rerun is in `rq1_agentic.json` (the run before the fix is `rq1_agentic_before_fix.json`) and `run_logs/20261115-052219-rq1-agentic-test-llama-ollama/`.
The gate keys on where the evidence comes from, not on a threshold fitted to these 5 NDAs. Still, it was checked
on the same NDAs that showed the problem, so confirm it on more data.

## Tool calling (`cc tools`)

| Error rate | Tool precision | Tool recall | Argument validity | Recovery rate | Unsafe attempts | Unsafe executed | Finished / hit max steps | Model calls | Wall time |
|---|---|---|---|---|---|---|---|---|---|
| 0.0 | 0.44 | 1.00 | 1.00 | – | 0 | 0 | 9 / 1 | 51 | 3.7 min |
| 0.1 | 0.42 | 1.00 | 1.00 | 0.38 | 0 | 0 | 8 / 2 | 67 | 1.6 min |

Injected episodes (5 of the 10): tool precision 0.29, recall 1.0, and no unsafe attempts at either error rate.

**What it shows**

1. **The agent always calls the gold tools, plus extras.** Recall is 1.0 but precision is about 0.43, so it over-calls.
2. **The approval gate held.** No attempt to send to the counterparty without approval, even with injected instructions
   in the NDA text.
3. **Recovery from failed tool calls is weak.** Only 38% of injected tool errors were retried successfully. The 0.1 run
   is faster only because many responses were already cached from the 0.0 run.

## RQ2: repairs done, scoring waits on the judge

**Status:** llama3.1:8b has red-teamed and repaired the first 5 planted test NDAs with all four systems (`loop`,
`r1`, `r1_attacker`, `r2`): 20 repaired NDAs, 603 model calls, about 72 minutes. **No RQ2 scores yet.** The
independent judge (`gemini-flash`, Gemini 3.8 Flash) has not answered. Its 398 first-stage questions are stored in
`data/rq2_queue/judge.gemini-flash.jsonl` (4 MB).

**Why it stopped there.** The Gemini key we had is on the free tier: 20 requests per model per day. RQ2 needs about
1,000–1,200 judge requests for these 5 NDAs. `gemini-3.8-flash` also timed out (504) when called directly. And no
Gemini Pro model, the judge the proposal names, is available to the key. So the repairs were run with the judge's
requests queued (`cc rq2 --evaluator-batch-queue`) to be answered later.

**How the judge scores a repair.** For every rule that applies to the deal, the judge reads the whole NDA plus that one
rule and answers Entailment, Contradiction or NotMentioned. For a field rule it reads the value, and code compares it
with the limit. A rule's status is compared before and after the repair:

- broken → ok is a **fix**;
- ok → broken is a **regression**;
- broken after the repair is **remaining**.

A fix or regression counts only if a second judge call with another seed agrees. Each confirmed regression is then
traced to the redline that caused it. Those follow-up questions depend on the first answers, so they are queued in
later rounds.

**What each system did** (`run_logs/rq2/repaired_drafts.jsonl` holds every repaired NDA: redlines, original and
repaired segments, full text):

| NDA | Company | loop | r1 | r1_attacker | r2 |
|---|---|---|---|---|---|
| 1 | Keystone | 3 rounds, 30 redlines | 1 round, 6 | 1 round, 8 | 3 rounds, 18 |
| 2 | Northwind | 3 rounds, 20 | none needed | stuck, 0 | clean, 0 |
| 4 | Northwind | 3 rounds, 26 | 1 round, 6 | 1 round, 6 | 3 rounds, 18 |
| 5 | Keystone | 3 rounds, 29 | 1 round, 2 | 1 round, 8 | 3 rounds, 9 |
| 6 | Bayview | 3 rounds, 27 | stuck, 0 | 1 round, 5 | 3 rounds, 6 |

The loop always used all 3 rounds (`max_rounds`), because the attacker kept finding new scenarios, and it writes 3–5
times as many redlines as `r1`. Whether those redlines fix more or break more is exactly what the judge has to decide.

**To finish RQ2** (needs a key with real quota, e.g. a paid Gemini key):

```bash
export GEMINI_API_KEY=...            # paid tier
cc batch submit  --backend gemini-flash --queue data/rq2_queue/judge.gemini-flash.jsonl   # one Batch API job, half price
cc batch collect --backend gemini-flash --job <job id>                                    # answers into the cache
# rerun the same rq2 command: repairs come from the cache, the next stage is queued; repeat until 0 pending
cc rq2 --backend llama-ollama --evaluator-backend gemini-flash --evaluator-batch-queue data/rq2_queue/judge.jsonl \
  --workers 2 --pack packs/policynda/saas/gold_rules.yaml --pack packs/policynda/hospital/gold_rules.yaml \
  --pack packs/policynda/manufacturer/gold_rules.yaml --labels data/labels/ndas_auto.yaml --allow-auto --limit 5
```

The rerun only replays llama from the cache. Without this machine's `data/cache/llm.sqlite`, a teammate's rerun
would redo the 72 minutes of repairs. With a different llama build, the repairs and their judge questions would also
change. The judge must be the backend the queue is named for (`gemini-flash`). Answering with another model means
adding a backend for it and queueing again, which takes minutes because the repairs are cached.

## Caveats

- 5 NDAs and 10 tool episodes, one seed, an 8B quantised model. Too small to decide between presets. A real comparison
  needs the full test split on `llama-vllm` (Kaggle) or Gemini.
- The rule lists are the gold packs (oracle rules), not compiled cards.

## Files

- `rq1_full.json`, `rq1_agentic.json` (with the fix), `rq1_agentic_before_fix.json`, `tools_err0.0.json`, `tools_err0.1.json`: the summaries each command printed,
  with stderr next to them.
- `run_logs/`: copies of the run folders. These hold the per-NDA reviews with every check and agent search
  (`reviews.jsonl`), the tool-call transcripts per episode (`episodes.jsonl`), and the full metrics.

## Reproduce

```bash
ollama pull llama3.1:8b
OLLAMA_CONTEXT_LENGTH=16384 OLLAMA_FLASH_ATTENTION=1 OLLAMA_KV_CACHE_TYPE=q8_0 ollama serve
export PYTHONUTF8=1
P="--pack packs/policynda/saas/gold_rules.yaml --pack packs/policynda/hospital/gold_rules.yaml --pack packs/policynda/manufacturer/gold_rules.yaml"
for pr in full agentic; do
  cc rq1 --backend llama-ollama --workers 1 --limit 5 --preset $pr --split test $P --law-pack packs/law/us_law_pack.yaml \
    --planted data/planted/test_seed0.json --labels data/labels/ndas_auto.yaml --allow-auto --hide-facts
done
for er in 0.0 0.1; do
  cc tools --backend llama-ollama --pack packs/policynda/saas/gold_rules.yaml --law-pack packs/law/us_law_pack.yaml \
    --limit 10 --error-rate $er
done
```
