# Cutting the API budget: local-first screening and its trade-offs

> **Update 22 Oct 2026 (audit, newdesign.md §19):** the totals below leave out the RQ2 judge, pack generation and
> auto labels. Current estimate: ≈ $60 before 31 Dec 2026 and ≈ $110 after (proposal §10). See "Added after the
> audit" at the end. Hosted Llama-8B on Together is $0.18 per M tokens.

Written on 9 Oct 2026, in answer to Pavan: "can we make inference on local (Ollama) models first and only go for API
calls if they show good results?"

## Short answer

**Yes, and part of it is already in the design. The rest can bring the API bill from ≈ $105 down to about $40–45
(≈ $75 after 31 Dec 2026).** The idea works in two different places, and they behave very differently:

1. **Screen experiments locally, then run only the ones that matter on Gemini.** Safe, and it doesn't change any
   result. This gives most of the saving.
2. **Screen individual calls locally (a cascade): Llama answers first, and Gemini is called only when Llama is unsure.**
   This saves more, but it changes *what system you are measuring*. It is fine as a feature of CounselCopilot, but
   not as a shortcut for "the Gemini results".

## Where the money goes today (newdesign.md §12)

| Item | Now (intro price) |
|---|---|
| Stage 2 on Gemini Flash: B1–B4, Full, 6 ablations × 123 NDAs (~1,350 runs × ~50k in / 5k out) | $38 |
| RQ2 on Gemini: loop, R1, R2, 4 loop ablations | $30 |
| Silver frames, policy compilation, policy prose (Gemini Pro) | $20 |
| Corpus-size sweep (40k / 150k / 400k) | $10 |
| Pro reference verifier | $8 |
| **Total** | **≈ $105** |

Stage 1 (Llama-3.1-8B on Kaggle) is already free. Nearly all the cost is stage 2, so that is where to cut.

## Option 1: experiment-level screening (recommended)

Run everything on Llama first, which we already do. Then send to Gemini **only** the comparisons the paper's claims
rest on:

- **On Gemini:** Full, B1, B2, B4, plus the two ablations that test RQ1 (no applicability filter, no reverse
  retrieval). For RQ2: the loop, R1 and R2.
- **Llama only:** all other ablations (planner, verifier, memory, round count, the different-model attacker). If an
  ablation shows no effect on Llama, the Gemini run would add nothing; if it shows a large effect, one Gemini run on
  the 40-NDA subset is enough to confirm it.

**Trade-off:** the paper says "ablations on Llama, headline results on both". That is normal and honest. The brief
asks for ablations, not ablations on every backbone.

## Option 2: stop paying for the same tokens twice

These change no results.

- **Response cache:** store every API response keyed by a hash of the prompt. A re-run after a crash, or after a
  scoring bug fix, costs $0.
- **Smoke test first:** run 5 NDAs on Gemini before every batch job. Most wasted money comes from a broken prompt
  running on 123 NDAs.
- **Context caching:** the system prompt, tool schemas and law pack are identical in every call, so cache them (Gemini
  context caching).
- **Cap the context:** the ~50k input per run is an upper estimate. With retrieval capped at a fixed top-k, ~20–25k
  is realistic. Report the cap, since equal budgets are already part of the fairness rule.
- **Cheaper models where quality barely matters:** Flash instead of Pro for silver frames and policy prose (a teammate
  hand-checks them anyway); Flash-Lite for the planner.
- **Develop on the free tier**; use the Batch API (50% off) for every real run.
- **Drop to stretch:** the 400k sweep point and the Pro reference verifier.

## Option 3: a per-call cascade (Pavan's idea, as a system feature)

Llama and our QLoRA model run locally on every check. Only findings they are **unsure about** go to Gemini:

- low confidence;
- the tuned and prompted models disagree;
- or a high-severity rule.

The known name for this is an LLM cascade (FrugalGPT; Chen et al., 2023).

**What it is good for:**
- It cuts tokens a lot, because most rule checks are easy ("is there a governing-law clause?").
- It is a real deployment benefit: cheaper, and most NDA text never leaves the company.
- It is easy to measure: tokens per NDA, and the share of calls escalated.

**The trade-offs:**
- **It changes what you measure.** A cascaded run is a Llama+Gemini hybrid, not Gemini. So we can't use it to *save
  money on the Gemini results*. We would report it as its own configuration, "Full (local-first)", next to "Full
  (Gemini)".
- **Silent misses.** If Llama is confidently wrong ("no violation"), the finding is never escalated, and nobody sees
  it. 8B models are often over-confident. Fix: set the escalation threshold on dev against gold labels, always
  escalate high-severity rules, and report missed-defect rate by severity.
- **"Predicting" whether Gemini will do better is itself uncertain.** Measure it first: run both models on the 61 dev
  NDAs, then check how often they agree and whether Llama's confidence tracks its errors. If agreement is low, the
  cascade won't save much.
- **More engineering:** one more component to build and tune.
- **Ollama vs Kaggle:** Ollama on a laptop is fine for prompt development on a few NDAs. For full runs (123 NDAs ×
  many systems × 2 seeds), vLLM on Kaggle is much faster because it batches requests.

## New estimate with options 1 + 2 (option 3 not counted)

| Item | New (intro price) |
|---|---|
| Stage 2: 6 configurations × 123 NDAs, ~25k in / 5k out, batch + caching | ≈ $15 |
| RQ2: loop, R1, R2 × 123 NDAs | ≈ $13 |
| Silver frames and policy prose with Flash; policy compilation with Pro (once) | ≈ $10 |
| Sweep at 40k and 150k only, 40 NDAs | ≈ $4 |
| Pro reference verifier | stretch, $0 |
| **Total** | **≈ $40–45** (≈ $75 from 2027) |

## Recommendation

Do options 1 and 2 now; they cost nothing in rigour. Add option 3 as an optional "local-first" configuration only if
time allows, and present it as a cost and privacy result, never as a substitute for the Gemini numbers.

## Added after the audit (22 Oct 2026)

| Item | Estimate (intro price) |
|---|---|
| RQ2 independent judge (Gemini Pro, batch), 40-NDA subset, before/after plus confirmation runs | ≈ $12 |
| Policy packs and labels: written by Claude agents in the project (23 Oct 2026), no API | $0 |
| **New total with the table above** | **≈ $60** (≈ $110 from 2027) |

