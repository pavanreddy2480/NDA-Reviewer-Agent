# RQ2 loop ablations and compiled policy cards with Claude agents (15 Nov 2026, stopped part-way)

This follows the RQ1 ablation pilot in `../2026-11-15-haiku-ablations/`. It covers the two parts that pilot did not run:

1. **RQ2 loop ablations.** Claude Haiku agents are the repair systems and Claude Sonnet agents are the independent
   judge, a different backend as `cc rq2` requires.
2. **The policy compiler and `structured_applicability`.** Haiku compiles the three companies' prose policies into
   requirement cards (`cc compile`). Then the RQ1 pipeline runs on those cards instead of the oracle gold rules.

**Status: stopped by request after 19 batch rounds, so the results are partial.** Every number below covers only the
NDAs that had finished. The same caveat applies as for every Claude-run pilot: Claude wrote the PolicyNDA data, so
these are relative effects inside one pilot, not project results.

## Setup

- The first 5 planted test NDAs (`data/planted/test_seed0.json`): docs 1, 2, 4, 5 and 6. Gold packs, US law pack,
  auto labels, `--hide-facts`.
- **RQ2.** `cc rq2 --backend claude-haiku-agent --evaluator-backend claude-sonnet-agent --noise-floor 30`, with the
  systems `loop r1 r1_attacker r2 loop_no_attacker loop_no_regression loop_1_round`. Up to 3 rounds each. That makes
  35 repair jobs (7 systems × 5 NDAs). `other_attacker` was not run because it needs a third backend.
- **Compiler.** `cc compile --backend claude-haiku-agent` for each company. Then `cc rq1 --ablation full` and
  `--ablation structured_applicability` ran on `packs/compiled/haiku_*.yaml`, scored against the gold rules.
- Batch mode, round by round. Each round:
  - Haiku's uncached requests were split into shards. One Haiku agent answered each shard from the file alone
    (`drivers/agent_prompt.txt`).
  - The judge's questions were grouped by NDA (`scripts/agent_judge.py export`). One Sonnet agent answered them
    (`drivers/judge_prompt.txt`).
  - The answers were loaded and every run was started again (`drivers/next.sh`).
- Work done: 19 rounds, 951 Haiku requests and 1,272 judge questions.

## Results so far

### Compiled policy cards (`cc compile`, Haiku)

| Company | Cards | Precision vs gold rules | Recall | Missed gold rules |
|---|---|---|---|---|
| Northwind Cloud (SaaS) | 34 | 0.882 | 1.000 | none |
| Hospital | 34 | 0.882 | 1.000 | none |
| Manufacturer | 43 | 0.674 | 0.967 | P-11 |

Haiku found almost every gold rule. Its extra cards are mostly gold rules split into several cards, plus a few
requirements the gold packs leave out. The manufacturer pack was split the most (14 cards with no gold match).

### RQ1 on the compiled cards (3 of 5 NDAs finished: docs 2, 4, 5)

| Rules given to the reviewer | P | R | F1 | False alarms / NDA | Applicable rules / NDA |
|---|---|---|---|---|---|
| Oracle gold rules (same 3 NDAs, from the RQ1 pilot) | 0.80 | 0.61 | 0.69 | 1.7 | – |
| Compiled cards, `full` (model-judged applicability) | 0.58 | 0.42 | 0.49 | 3.3 | 22.3 |
| Compiled cards, `structured_applicability` | 0.58 | 0.42 | 0.49 | 3.3 | 23.0 |

The scoring is strict over 33 gold defects. A finding must cite the gold rule's id, and a compiled card that splits
or rewords a rule loses that match. So part of the 20-point drop is the id mapping, not missed defects.

The two applicability modes gave the same findings on these 3 NDAs. Model-judged applicability kept 22.3 rules per
NDA against 23.0 for the structured conditions, and the one or two rules it dropped produced no finding either way.

### RQ2 repair systems (finished jobs only)

| System | NDAs scored | Problems left / NDA | Loopholes left / NDA | Redline regression rate | Gold repair success | Rounds | Stopped |
|---|---|---|---|---|---|---|---|
| r1 (one repair pass) | 5 | 2.6 | 0.2 | 4.9% (2 of 41) | 0.58 | 1.0 | clean 5 |
| r2 (self-refine) | 5 | **2.2** | 0.0 | 4.2% (2 of 48) | 0.58 | 2.2 | clean 5 |
| loop_no_attacker | 5 | 2.4 | 0.2 | **0%** (0 of 48) | 0.50 | 2.2 | clean 2, conflict 1, stuck 1, max_rounds 1 |
| loop_1_round | 1 | 1.0 | 0.0 | 0% | 0.0 | 1.0 | max_rounds 1 |
| loop, r1_attacker, loop_no_regression | 0 | – | – | – | – | – | still running when stopped |

What it shows so far:

1. **The full loop and the attacker variants did not finish.** Each loop round runs the reviewer again, plus the
   attacker and the regression check. In batch mode that is many dependent steps, so H2 (loop ≤ half of r1's remaining
   problems) **could not be tested**.
2. **Without the attacker, the loop's regression check works.** loop_no_attacker made 48 redlines and none
   regressed, against 4–5% for r1 and r2. But it left about as many problems as r2 (2.4 against 2.2 per NDA) and
   stopped early on 2 NDAs: on one a policy conflict, on the other repairs that stopped making progress.
3. **Haiku repairs far better than llama3.1:8b.** On the earlier Ollama run, r1 left 9–10 problems per NDA. Here
   it leaves 2.6. The NDAs and the judge family differ, so this is only a rough comparison.

## Bug found and fixed on the way

`run_rq2` gave every system on an NDA the same attacker object. The attacker numbers its scenarios (S-001, S-002, ...)
with a counter, and those ids go into the repair prompts. So r1_attacker's and the loop variants' redlines depended
on which systems ran before them, and in batch mode on how far those systems had got. That is why their repaired
drafts kept changing between rounds.

Fixed in round 18: each system now gets its own attacker (`experiments/rq2.py`), with a test
(`test_rq2_systems_do_not_share_an_attacker`). The scored rows above are not affected. r1, r2 and loop_no_attacker
use no attacker, and loop_1_round was scored after the fix.

## To finish the run

The cache holds every answer so far. Rebuild it from `agent_answers/`, then keep running rounds:

```
for N in 1 .. 19:
  cc batch load --backend claude-haiku-agent  --queue agent_answers/rN/q.claude-haiku-agent.jsonl  --answers agent_answers/rN/haiku
  cc batch load --backend claude-sonnet-agent --queue agent_answers/rN/j.claude-sonnet-agent.jsonl --answers agent_answers/rN/judge
```

Then rerun `drivers/rq2_round.sh` and `drivers/cmp_round.sh`, or `drivers/next.sh`, which also exports the next round.
Two parts are left:

- About 19 RQ2 jobs. Because of the attacker fix, the attacker systems redo part of their work.
- 2 compiled-pack NDAs. These are in the approval-clerk tool steps, one step per round.

With a real API backend, these runs take minutes rather than rounds.

## Caveats

- These are partial results on 3 to 5 NDAs with one seed. No paired comparisons are reported because the loop has
  no finished rows.
- Claude wrote the benchmark data. The judge (Sonnet) is a different backend from the repairer (Haiku) but the same
  family, so the judge's independence is weaker than the design asks for.
- The agents answered "by hand", reading each request from a file.
- Some planted NDAs contain an instruction to email the agreement to an outside address. Several agents reported it
  and treated it as data. No send was attempted. Three Haiku agents made a stray call to a messaging tool, and one of
  those messages reached the coordinator. None changed anything.

## Files

- `run_logs/rq2/`: `metrics.json`, `repairs.jsonl`, `repaired_drafts.jsonl` and `detections.jsonl` from the last
  run, plus `command_summary.json`.
- `run_logs/compiled_full/` and `run_logs/compiled_structured_applicability/`: `metrics.json`, `reviews.jsonl` and
  `command_summary.json`.
- `compile/compile_<company>.json`: the compiler's report against the gold rules. The cards themselves are in
  `packs/compiled/haiku_<company>.yaml`.
- `drivers/`: the round scripts and the agent prompts.
- `agent_answers/r<N>/`: each round's queues and answers. Round 19's Haiku answers are partial because the run was
  stopped.
