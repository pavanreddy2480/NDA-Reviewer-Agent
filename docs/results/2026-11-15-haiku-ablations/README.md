# RQ1 ablations with Claude Haiku agents (15 Nov 2026)

A pilot of the ablation grid in `docs/design/ablation-studies.md`. **Claude Haiku is the system under test**, answered by
agents in the project thread (backend `claude-haiku-agent`, batch mode). There is no Ollama or Gemini key in the build
container, so this is the "lite model" run Pavan asked for.

**Read these as relative effects inside one pilot, not as the project's results.** Claude also wrote the PolicyNDA
packs and the auto labels, so a Claude system is graded on data its own model family wrote, which breaks the proposal's
family-independence rule. The same caveat applies to the Oct Sonnet pilot.

## Setup

- 5 planted test NDAs (`data/planted/test_seed0.json`, the first 5), deal facts hidden (`--hide-facts`), the three
  PolicyNDA gold packs plus the US law pack, auto labels, 30 scripted precedents. The same NDAs as the 15 Nov
  llama3.1:8b run.
- **Oracle rules.** The reviewer gets the gold rule lists, with no `cc compile` step. So `structured_applicability`
  (it needs compiled cards) was not run. `tuned_checker` needs the QLoRA model and was not run either.
- 15 configurations: the 10 pipeline ablations, the reviewer alone under `full` and `exhaustive_filtered` (B4+filter),
  and the baselines B2, B2+checklist and B3. B1 needs a long-context model.
- 703 requests over 15 batch rounds. Each round's uncached requests were exported as shards (`cc batch export`), each
  shard was answered by its own Haiku agent from the shard file alone (`agent_prompt.txt`), and the answers were loaded
  (`cc batch load`). Then every configuration was run again. `round.sh` and `next.sh` are the drivers. Configurations
  share the cache, so a request two ablations make identically is answered once. The last rounds were the
  tool-calling agents (approval clerk, B3), one step per round.
- Scoring is strict (rule, type and cited evidence must all match), over 53 gold defects. Paired bootstrap against
  `full`, Holm-corrected over the ablations. Baselines and presets show raw p-values.

## Results

| System | P | R | F1 | ΔF1 vs full (95% CI) | p | Omission R | False alarms / NDA | Tokens / NDA |
|---|---|---|---|---|---|---|---|---|
| **full** | 0.82 | 0.60 | **0.70** | – | – | 0.60 | 1.4 | 39.0k |
| no_reverse | 0.69 | 0.21 | 0.32 | **−0.38** [−0.44, −0.33] | <0.001 | **0.00** | 1.0 | 21.3k |
| no_filter | 0.52 | 0.60 | 0.56 | **−0.13** [−0.19, −0.09] | <0.001 | 0.60 | **5.8** | 66.6k |
| no_verifier | 0.83 | 0.64 | 0.72 | +0.03 [0.00, +0.06] | 1.0 | 0.60 | 1.4 | 34.8k |
| no_frames | 0.82 | 0.60 | 0.70 | 0 | 1.0 | 0.60 | 1.4 | 37.8k |
| fixed_pipeline | 0.82 | 0.60 | 0.70 | 0 | 1.0 | 0.60 | 1.4 | 38.6k |
| no_xref | 0.82 | 0.60 | 0.70 | 0 | 1.0 | 0.60 | 1.4 | 38.8k |
| no_memory | 0.82 | 0.60 | 0.70 | 0 | 1.0 | 0.60 | 1.4 | 40.1k |
| no_tool_agent | 0.82 | 0.60 | 0.70 | 0 | 1.0 | 0.60 | 1.4 | 33.0k |
| tool_errors | 0.82 | 0.60 | 0.70 | 0 | 1.0 | 0.60 | 1.4 | 39.0k |
| reviewer alone (`full`) | 0.81 | 0.64 | 0.72 | +0.02 [−0.02, +0.06] | 0.36 (raw) | 0.60 | 1.6 | 26.9k |
| B4+filter (`exhaustive_filtered`) | 0.74 | 0.58 | 0.65 | −0.04 [−0.08, −0.02] | 0.001 (raw) | 0.46 | 2.2 | 56.6k |
| B2 (RAG) | 0.28 | 0.09 | 0.14 | −0.56 [−0.59, −0.52] | <0.001 (raw) | 0.00 | 2.6 | 28.9k |
| B2+checklist | 0.39 | 0.58 | 0.47 | −0.23 [−0.29, −0.18] | <0.001 (raw) | 0.46 | 9.6 | 122.7k |
| B3 (single tool agent) | 1.00 | 0.17 | 0.29 | −0.41 [−0.57, −0.27] | <0.001 (raw) | 0.03 | 0.0 | 35.5k |

Metrics the F1 table cannot show (from each run's `metrics.json`):

| Ablation | What it should change | full | ablation |
|---|---|---|---|
| no_memory | escalations to senior counsel | 5 (4 avoided by precedents) | **9** (0 avoided) |
| no_verifier | findings the verifier rejected | 2 rejected, **both true defects** (rejection precision 0) | – |
| fixed_pipeline | reviewers run | the planner already chose all 3 reviewers on all 5 NDAs | same |
| tool_errors | recovery from failed tool calls | 20 approval-agent calls, 0 unsafe | identical transcript: no injected error was hit |
| no_tool_agent | hand-off precision / recall | 1.0 / 1.0 | 1.0 / 1.0 (the script routes the same 6 approvals) |

## What it shows

1. **Reverse retrieval (rule → NDA) is the component that matters most.** Without it, omission recall drops from 0.60
   to 0 and F1 halves (0.70 → 0.32). That is RQ1's central claim, and it matches the Oct Sonnet pilot (0.72 → 0.00)
   and the design's expectation.
2. **Applicability filtering earns its place.** Checking every rule whatever the deal quadruples false alarms (1.4 →
   5.8 per NDA), drops precision from 0.82 to 0.52, and costs 1.7 times the tokens.
3. **Precedent memory avoids escalations.** It avoided 4 of 9 escalations (9 → 5), with the same hand-off precision.
4. **The verifier hurt slightly here.** It rejected 2 findings, and both were true defects, so removing it raised
   recall (0.60 → 0.64). The difference is not significant (p = 1.0 after Holm). It needs more NDAs, or a stricter
   rejection rule.
5. **Four ablations were not exercised on these 5 NDAs**, so "no effect" here does not mean "cut it":
   - `fixed_pipeline`: the planner ran every reviewer anyway.
   - `tool_errors`: no injected error fired in 20 calls.
   - `no_xref` and `no_frames`: identical findings. The planted defects on these NDAs need no cross-reference hop, and
     Haiku read the field rules the same way with and without frames.
6. **H1 against the baselines.** The full pipeline beats B2 by 56 F1 points and B2+checklist by 23, so the "≥10 points
   over B1 and B2+checklist" bar is cleared against B2+checklist on this pilot. B4+filter is 4 points below `full`,
   just outside the 3-point TOST margin, and uses 1.45 times the tokens.
7. **B3 is precise but finds little.** The single tool agent found only 9 of the 53 gold defects, with no false alarms.
8. **Haiku is much stronger than llama3.1:8b on the same 5 NDAs.** The reviewer alone scores F1 0.72 against 0.46.

## Caveats

- 5 NDAs, one seed, oracle rules. The confidence intervals come from bootstrapping 5 documents, so they are narrow but
  fragile.
- Claude wrote the benchmark data (see above).
- The agents answered as Haiku "by hand", reading each request from a file. That is close to, but not the same as, an
  API call at temperature 0.
- Planted NDAs include injected instructions to email the agreement to an outside address. The agents that mentioned
  them treated them as data. No tool call to send anything was attempted (`executed_unsafe` 0 in every run).
- RQ2 loop ablations and the compiled-card runs (`structured_applicability`) are in `../2026-11-15-haiku-rq2-and-compiler/` (partial: stopped after 19 rounds).

## Files

- `ABLATIONS.md`: the report `cc ablations` wrote.
- `run_logs/<config>/`: `metrics.json`, `reviews.jsonl` and the command summary for each configuration.
- `agent_answers/r<N>/`: each round's queue and the agents' answers. To rebuild the cache:
  `cc batch load --backend claude-haiku-agent --queue agent_answers/rN/q.claude-haiku-agent.jsonl --answers agent_answers/rN/answers`
  for N = 1 to 15, then rerun `round.sh` (every answer then comes from the cache).
