# Ablation studies (design, 14 Nov 2026)

What each ablation removes, what it tests, what we expect, and how it is scored. The proposal's
ablations row (§7) is the source. Run everything with `scripts/run_ablations.sh`; the results
land in `runs/ablations/ABLATIONS.md`.

## 1. Setup

| | Choice | Why |
|---|---|---|
| Data | PolicyNDA test split: 123 ContractNLI NDAs with planted defects (`data/planted/test_seed0.json`), 3 company packs, US law pack | The benchmark the proposal scores |
| Rules | Compiled requirement cards from prose (`cc compile`, Gemini Pro), scored against the gold rule lists | The real system never sees gold rules. `ORACLE=1` gives an upper bound only |
| Deal facts | Hidden (`--hide-facts`): personal data and governing law are read from the NDA | The H1 headline setting |
| Stage 1 | Every ablation on **Llama-3.1-8B through local Ollama** (`llama-ollama`) | Free, so the whole grid fits |
| Stage 2 | Full system, B1, B2, B2+checklist, B4+filter and 2 ablations (no reverse, no filter) on **Gemini Flash** | Confirms the stage-1 effects hold on a stronger model |
| RQ2 judge | Gemini Pro (`gemini-pro`), never a repair system's model | Independent evaluator |
| Other attacker | Qwen3-14B through Ollama (`qwen-ollama`) | "Attacker on a different model" |
| Seeds | Seed 0 by default; `SEEDS="0 1 2"` gives the proposal's 3 deal and defect draws | Variance across draws |

**One change per ablation.** Every ablation is the full pipeline with exactly one component
switched off (`PipelineConfig.ablation`), on the same NDAs, rules, deals and model.

## 2. RQ1 ablations (pipeline, stage 1)

| Ablation | What changes | Question | Expected vs full | Metric that should move |
|---|---|---|---|---|
| `no_reverse` | Forward retrieval only (clause → rule) | Does rule → NDA retrieval find the omissions? **The clean RQ1 test** | Large drop | Omission recall (the pilot: 0.72 → 0.00) |
| `no_filter` | Every rule checked, whatever the deal | Does applicability filtering cut false alarms? | More false alarms, lower precision | False alarms per NDA |
| `no_frames` | Field rules read by per-field questions, not obligation frames | Do frames read terms (durations, law, notice) better? | Lower recall on field rules | Violation recall |
| `no_verifier` | Findings go out without the citation check | Does the verifier remove unsupported findings without losing true ones? | Lower precision, same recall | Precision; verifier rejection precision |
| `fixed_pipeline` | Planner replaced by "run every reviewer" | Does planning save work without missing defects? | Same F1, more tokens | Tokens per NDA |
| `no_xref` | No cross-reference graph (no one-hop expansion, no inherited approvers) | Do linked clauses matter for approvals and exceptions? | Lower approval-needed recall | Approval-needed recall |
| `no_memory` | No precedent memory at the approval desk | Do precedents avoid needless escalations? | More escalations | Escalations per NDA; hand-off precision |
| `no_tool_agent` | Scripted approval hand-off instead of the tool-calling agent | Does the agent route approvals better than a fixed script? | Lower hand-off precision | Hand-off precision / recall |
| `structured_applicability` | Cards use structured `applies_if` instead of model-judged applicability | Is model-judged applicability better on prose policies? | Lower F1 | F1, precision. *Only meaningful with compiled packs (not `ORACLE=1`)* |
| `tool_errors` | 10% of tool calls fail | Does the agent recover from tool failures? | Small F1 drop | Recovery rate; unsafe attempts must stay 0 |
| `tuned_checker` | Checker is the QLoRA adapter (`TUNED=llama-tuned`) | Does fine-tuning help, on held-out hypotheses too? | Higher F1 and omission recall | F1, omission recall |

Run beside them, for H1 (not ablations): reviewer alone (`reviewer:full`), B4+filter
(`reviewer:exhaustive_filtered`, TOST within 3 points), and the baselines B2, B2+checklist, B3
(B1 long context only on Gemini).

## 3. RQ2 ablations (repair loop, stage 1, 40 NDAs)

| System | What changes | Question |
|---|---|---|
| `loop` | Full: attacker, repairer, full re-check, up to 3 rounds | |
| `loop_no_attacker` | No opposing counsel; repair only the reviewer's findings | Do attacks find problems worth fixing? |
| `loop_no_regression` | No re-check after the repair | Does the re-check stop repairs that break other rules? (regression rate) |
| `loop_1_round` | One round instead of three | Do extra rounds pay for their tokens? |
| loop, other attacker | Attacker on Qwen3-14B | Is a different-model attacker better at finding loopholes? |
| `r1`, `r1_attacker`, `r2` | Baselines: one-shot, one-shot with the attack scenarios, self-refine | H2 |

Primary metric: remaining problems per NDA after repair, as judged by the independent
evaluator, reported as the ratio loop ÷ system with a paired bootstrap CI. Below 1 means the full
loop leaves fewer problems. Secondary: regression rate, repair success on planted defects,
loopholes left, rounds, tokens per NDA.

## 4. Cascade (offline, from runs)

Local-first cascade from the stage-1 and stage-2 `reviewer:full` runs: a check goes to Gemini
only when Llama is unsure (and, in the second variant, also for high-severity rules). Reported:
the F1 vs escalation-share curve, the threshold chosen within 1 F1 point of all-Gemini, and the
calibration (ECE) of Llama's confidence.

Not in the script: the **policy-size sweep** needs a folder of public policy documents for
padding (`cc sweep --padding DIR`, then compile and run `rq1` on each size).

## 5. Statistics

- Every ablation is compared with `full` on the same NDAs: paired bootstrap of the micro
  P/R/F1 difference (5,000 resamples). The p-value is two-sided.
- The ablations are one family, so their p-values are **Holm-corrected**. Baselines and presets
  are shown with raw p-values.
- An effect counts when the Holm-corrected p is below 0.05 **and** it moves in the expected
  direction. An ablation that changes nothing (CI includes 0) is reported as "no measurable
  effect", and the component is a candidate to cut.
- With 3 seeds, report each seed's table and the mean difference. Conclusions should hold on
  every seed.

## 6. Running it

```bash
ollama pull llama3.1:8b && ollama pull qwen3:14b
OLLAMA_CONTEXT_LENGTH=16384 ollama serve           # in its own terminal
pip install -e '.[gemini]' && export GEMINI_API_KEY=...
STAGES="compile rq1" LIMIT=20 scripts/run_ablations.sh    # first pass, a few hours
scripts/run_ablations.sh                                 # everything
```

Every answer is cached in `data/cache/llm.sqlite`, so a stopped run resumes, and ablations that
share checks with `full` reuse them.

**Rough load, measured on a 6-NDA dry run** (the request counts are real; the times assume
about 2 s per local request with 2 in parallel):

| Stage | Requests | Time / cost |
|---|---|---|
| Stage-1 RQ1 grid, 123 NDAs | about 500 per NDA before caching, about 250 after | about 15–20 h locally (LIMIT=40: about 6 h) |
| Stage-2 Gemini Flash RQ1 | about 390k tokens per NDA before caching | about $10 for 40 NDAs, about $30 for all 123 |
| RQ2, 40 NDAs, 7 systems | about 9k local; the Gemini Pro judge reads about 1M tokens per NDA | judge about $70 on Pro, about $30 with `JUDGE=gemini-flash` |
| Compiler | 3 packs once | under $1 |

The RQ2 judge is the biggest cost. Start with `RQ2_LIMIT=20`, or use `JUDGE=gemini-flash`.

## 7. Threats

- An 8B model may be too weak for some components to show an effect (for example the verifier),
  which is why stage 2 repeats the key ablations on Gemini.
- Packs and labels were written by Claude and are not yet human-checked; ratios between systems
  are less affected than absolute scores.
- `structured_applicability` and the compiler effects only make sense on compiled packs.
- The dry run used an offline keyword model; its numbers check the plumbing and are not results.
