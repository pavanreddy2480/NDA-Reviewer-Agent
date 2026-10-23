# CounselCopilot: audit against prop.pdf

> **Historical document.** Kept as a record of its date. The current design is `newdesign.md` (v6; §19 lists the 22 Oct 2026 audit fixes), and the current proposal is `proposal/proposal.tex`.

Audit of `newdesign.md` (first version saved as `newdesign_v1.md`) against every requirement in prop.pdf. 2 Oct 2026.
Team decisions applied: **India** jurisdiction, **Llama-3.1-8B first, then Gemini Flash** as the backbone (added after this audit; see newdesign.md §3.2), **both speculation mechanisms kept**.

## Verdict

**The project stands. It does not need replacing, but it needs the eight fixes below before it goes to the TA.**
It is in a listed domain (Legal), close to the brief's own direction D, safe, and feasible. Its research angles
(omissions, applicability, speculation in a drafting setting) go beyond direction D.
The first version had three problems a careful TA would catch:
1. **Circular evaluation.** We would write the policies, write the rules, plant the defects and build the checker,
   so a good score would prove little.
2. **The RAG justification breaks with Gemini Flash.** We said the policy packs "don't fit in one prompt". Gemini
   Flash has a ~1M-token window, and our packs are ~40k tokens each.
3. **The speculation gains were mostly simulated.** Prefetching local lookups saves milliseconds. The real wait is
   the LLM call, and the latencies were ones we chose ourselves. Speculative RAG's latency gain also disappears when
   the drafter is a 7B model on a free T4 GPU and the verifier is Gemini Flash, which is faster than the drafter.

All three are fixable, and the fixes make the project stronger. Details follow.

## Requirement-by-requirement check

| prop.pdf requirement | v1 status | After fixes |
|---|---|---|
| §1 Research oriented, not "another RAG app" | OK, but RQ2 read as engineering | RQ2 now targets the real bottleneck (fix 4) |
| §2 Each capability justified + measured | RAG and fine-tuning justifications weak under Gemini Flash | Re-justified (fixes 3, 6) |
| §2 Reasoning: analyse intermediate steps | Partly: metrics listed, no step-level ground truth | Gold applicability decisions per rule per NDA give step-level ground truth (fix 1) |
| §2 Tool calling: right tools, valid args, recovery, never unsafe | Metrics listed, but no definition of "right tool" | Gold tool trajectories defined per defect type (fix 7) |
| §3 Domain with datasets | OK (ContractNLI, CUAD) | Stronger: rules anchored to expert labels |
| §4 Narrow scope | Too many parts (3 fine-tunes, 2 speculation methods, 4 reviewers, 12+ configs) | Trimmed (fix 5) |
| §5 Compute budget with GPU-h, tokens, runs | Generic "small hosted API" | Recomputed for Gemini Flash, including rate limits (fix 8) |
| §6 Safety plan | OK | Adds a note that no member is a lawyer, and how law-pack errors are limited |
| §6 Distinct enough for a workshop | Novelty claimed but not sharp | Three crisp contributions (see below) |
| §7 Hypothesis with metric | **Missing.** RQs, no stated hypothesis or target | H1, H2 added with numbers (fix 2) |
| §7 Baseline | OK (long-context, naive RAG, single agent) | Plus a context-size sweep for the long-context baseline |
| §7 Eval set with known ground truth | Planted only, and unplanted natural defects in base NDAs would be miscounted | Fixed with ContractNLI-anchored rules (fix 1) |
| §7 Metric per capability | OK | Unchanged |
| §7 Ablation of each capability the RQ depends on | OK but too many | Core 6 on the full test set, the rest on a 40-NDA subset |
| §7 Tool-call accuracy + unsafe action rate | OK | Plus prompt-injection cases |
| §7 Qualitative examples, failure analysis | Mentioned only in the plan | Added explicitly to evaluation |
| §7 LLM judge validated on human labels | OK (100 labels, κ) | Unchanged |
| §8 All 14 proposal items | All present except an explicit hypothesis | Complete |

## The eight fixes (all applied in newdesign.md)

**Fix 1: Anchor policy rules to expert labels (solves circularity and ground-truth contamination).**
Problem: real ContractNLI NDAs naturally break or omit many of our synthetic rules. Unless we know every NDA's true
status against every rule, these unplanted defects get scored as false alarms.
Fix: most policy rules are written to map onto ContractNLI's 17 expert-labelled hypotheses. For example, "vendor
NDAs must require return or destruction of information" maps to *return of confidential information*, and "must
cover orally disclosed information" maps to *inclusion of verbally conveyed information*. Each NDA's label
(entailed / contradicted / not mentioned, with evidence spans) then gives the NDA's real status against the rule
for free:
- *not mentioned* = a **natural omission**;
- *contradiction* = a **natural violation**.

That gives an evaluation on **real, unplanted defects labelled by experts**, which is the strongest evidence a TA
could ask for. The remaining rules (governing law, term length, approval matrix) are hand-labelled on the 61 dev +
123 test NDAs. This is cheap because they are simple fields. Planted defects stay as a second, controlled test.

**Fix 2: State hypotheses with targets.**
- H1: two-way retrieval raises omission recall by ≥15 points over forward-only RAG at equal or lower false alarms
  per NDA.
- H2: speculative clause review cuts median time-to-feedback by ≥40% in live replay, with ≥98% of reused verdicts
  identical to a full re-run.

**Fix 3: Re-justify RAG for a 1M-context model.**
"It doesn't fit" is false for Gemini Flash. The real reasons:
- (a) Long-context models lose recall on items in the middle of long inputs, and an omission check needs *every*
  applicable rule checked.
- (b) Cost and latency per clause check.
- (c) Exact rule-ID citations.

We add a **policy-corpus size sweep**: pad each company pack with real public policy text to ~40k, ~150k and ~400k
tokens, and plot long-context vs RAG as the corpus grows. This turns a weak claim into a measured one, and real
companies have far more than 40k tokens of policy.

**Fix 4: Make live-mode speculation target the real bottleneck.**
Prefetching retrieval saves milliseconds; the review LLM call takes seconds. New mechanism, **speculative clause
review**:
1. While a clause is still being typed, the fine-tuned frame extractor predicts the finished clause's obligation
   frame.
2. The reviewer runs on that prediction in the background.
3. When the clause is finished, the real frame is extracted. If it matches the predicted frame on the fields the
   rules use, the speculative verdict is shown instantly. If not, the review re-runs.

Read-only prefetching is kept as the cheap first layer. The quality metric is the agreement between reused verdicts
and a full re-run. Latency uses **real measured** Gemini Flash call times, not chosen numbers. State-changing tools
are still never speculated.

**Fix 5: Trim scope.**
- One multi-task QLoRA model (clause tags, ContractNLI checks, obligation frames, and Speculative RAG drafts)
  instead of three.
- The separate tool-call predictor is dropped: the frame extractor now drives speculation, and a heuristic table
  covers prefetching.
- The dispute-risk reviewer is merged into the law reviewer (3 reviewers).
- Policy packs: 3 companies × ~30 rules (was ~60).
- Six core ablations on the full test set; the others on a 40-NDA subset.

**Fix 6: Re-justify fine-tuning and Speculative RAG honestly.**
The tuned model is justified by consistency and structured output (frames feed exact rule matching and drive
speculation), and by the brief's own test: does a tuned 7B match prompted Gemini Flash on ContractNLI and frame
extraction?
Speculative RAG is kept for **accuracy from source-separated drafts** (policy / law / precedent). Latency is
reported honestly, comparing a Gemini Flash-Lite drafter with the tuned 7B drafter. We expect no latency gain on
free GPUs and say so up front.

**Fix 7: Define gold tool trajectories.**
Each defect type has a required minimal set of tool calls. For example, an approval-gated deviation needs
`rule_lookup` → `approval_matrix_query` → `request_approval`. Tool-selection accuracy is then computed against this
set: missing calls count against recall, and extra calls count as waste.

**Fix 8: Budget for Gemini Flash, including rate limits.**
- The main runs are ≈ 123M input + 12M output tokens. At Gemini 2.5 Flash list prices ($0.30 per million input
  tokens, $2.50 per million output tokens; **check current prices**) that is ≈ $68.
- Subset ablations, the size sweep (with context caching), silver frames and Pro reference runs add ≈ $50.
  Total ≈ $120.
- The free tier's requests-per-minute limit would stretch the runs over weeks, so we plan on paid tier 1 for the
  experiment phase. Free tier is fine for development.
- GPU: ≈ 22 T4-hours on Kaggle, within the free weekly quota.

## Sharpened novelty (for the proposal)

1. **First open benchmark for checking NDAs against a company's own policies.** It includes *omissions*, and its
   ground truth is anchored to expert ContractNLI labels, covering both natural and planted defects.
2. **Two-way, applicability-aware retrieval**, with a measured comparison against long context as the policy
   corpus grows.
3. **Speculative clause review** for live drafting: a lossless-by-verification way to hide LLM latency in the human
   typing window, with a strict read-only boundary.

## Remaining risks the team should know

- **No team member is a lawyer.** The India law pack is limited to well-documented, clear-cut provisions (ICA s.23,
  27, 28; DPDP Act 2023 duties; arbitration seat basics). Each summary cites the official text and is checked by two
  teammates. Statutory flags are framed as "risk", never "illegal".
- **Direction D in the brief is close to this idea.** The TA will look for what is new beyond it; lead the proposal
  with the three contributions above.
- **Related-work pass still needed** on commercial playbook tools (LegalOn, Ironclad, Spellbook, Harvey) and on
  contract compliance checking, to show none has an open benchmark covering omissions.

## Alternatives, if the team would rather switch

I don't recommend switching. If you do, the two strongest fallbacks already written up are:
- the original NDA-Scrub proposal (`proposal/proposal.tex`), which is narrower and lower risk but less novel;
- option 4, "proving absence" (`project_idea_4_proving_absence.md`), which is the most novel but in a non-listed
  domain.

---

# Second pass (design v3, after the Llama → Gemini change)

**Verdict: the design now meets every requirement in prop.pdf §1–§8. It is ready to turn into the proposal.** The
second pass found no missing items, but it found four weaknesses a careful TA could raise. All four are fixed in
newdesign.md.

| # | Weakness found | Why a TA would care | Fix applied |
|---|---|---|---|
| 1 | The tuned model was trained on all 17 ContractNLI checks, and most policy rules are anchored to those same checks | Gains could come from memorised ContractNLI labels, not the pipeline; omission detection could look like plain ContractNLI classification | Train on 12 checks, hold out 5, report the held-out rules separately. The clean RQ1 comparison is the forward-only ablation (same model everywhere), not B2 |
| 2 | Live replay assumed consultants type every word at 40 wpm | Real drafting is mostly paste-and-edit, so typing-only overstates the speculation window and RQ2 | Two replay styles: typed and paste-and-edit, with RQ2 reported for both |
| 3 | On local Llama, speculative calls share the T4 GPU with the real review | Speculation could slow the real review, so latency savings would be overstated | Measure latency with speculation competing for the GPU, run it at low priority, report wasted GPU-seconds |
| 4 | The planner had no ablation | The brief says a capability added "only because it appears on this list" doesn't count; the agentic part needs evidence | New ablation: planner vs fixed pipeline (F1 and tokens) |

Smaller fixes:
- RQ2's wording now matches H2 (speculative clause review; Speculative RAG is secondary).
- ContractNLI fine-tuning uses retrieved spans (~512 tokens) so it fits a T4.
- Stage 2 runs 1 seed, so its statistics are bootstrap-only (stated).
- The rule base is compiled once with Gemini Pro and frozen, so both stages use the same rules.
- Precedent memory is pre-filled with ~30 scripted approvals.

## Final requirement check (v3)

| prop.pdf item | Where in newdesign.md |
|---|---|
| Title, domain, target user | Header, §0 |
| Problem statement (5–8 sentences) | §1 (7 points) |
| Research question(s) | §0: RQ1, RQ2 |
| Hypothesis with metric (§7) | §0: H1, H2 |
| Why it matters; what is missing | §1 points 5–7 |
| Each capability: why needed + metric | §9 table; details in §4–§6, §8.3 |
| Reasoning: intermediate steps analysed | §8.3 Reasoning row (per-rule applicability decisions vs gold; miss-cause table) |
| Tool calling: right tools, valid args, recovery, never unsafe | §8.3 Tool calling row (gold tool sets, injected errors, prompt injection) |
| Architecture + diagram | §3 (mermaid; to redraw in TikZ for the proposal) |
| Novelty | §0 "What is new" |
| Dataset / environment with known ground truth | §7 (ContractNLI-anchored natural defects + planted defects) |
| Baselines | §8.1 B1–B3 |
| Ablation per capability the RQs depend on | §8.2 |
| Tool-call accuracy + unsafe-action rate | §8.3 |
| Qualitative examples, failure analysis | §8.4 |
| LLM judge validated on human labels | §8.3 (100 labels, κ) |
| Compute plan (GPU-h, tokens, cost, runs) | §12: ≈ 50 T4-h, ≈ $80 API |
| Safety plan | §11 |
| Risks and fallback | §13 |
| Narrow scope | NDAs only, India only, 3 companies |
| No code before TA approval | §14 plan starts after approval |

**Remaining items for the team (not design gaps; items 1–2 closed in the third pass below):**
1. Confirm current Gemini pricing and credit.
2. Do the related-work pass on commercial playbook tools and on speculation over partial user input.
3. Compress this design into the 5-page proposal: lead with the three contributions and RQ1, and keep Speculative
   RAG to one line as the stretch goal.

---

# Third pass: related work and current pricing (2 Oct 2026)

The three open items are now closed. Two findings changed the design.

**1. PolicyGuard (arXiv 2606.32004, June 2026) is very close to our idea.** It checks NDAs against a company's
playbook by compiling the playbook into logic rules and checking each one. What it lacks:
- an open benchmark (it uses 5 confidential contracts);
- omissions as a first-class outcome;
- deal-specific applicability;
- any live drafting or speculation.

Changes made:
- Cited it.
- Added **B4: exhaustive per-rule checking** (PolicyGuard-style) as the strongest baseline for omissions.
- Revised H1: match B4's recall with ≥50% fewer checks and fewer false alarms from rules that don't apply.
- Narrowed the novelty claim to the open benchmark, applicability-aware reverse retrieval, and absence as a
  first-class outcome.

**2. Speculative Interaction Agents (arXiv 2605.13360, May 2026) already speculate on unfinished user input**
(streaming speech), with the same read-only/state-changing tool split we use. Their speedups cost a little accuracy.

Changes made:
- Cited them as the source of the tool split.
- Narrowed our claim to frame-equality verification (lossless reuse), review verdicts over document clauses, and the
  paste-and-edit drafting setting.

**Also added:** ContractEval (NLLP 2025), which finds open models wrongly answer "no such clause" in ~25–30% of
cases. This supports our focus on reliable absence judgements. CLAUSE is now cited as Findings of EACL 2026.

**Pricing (official Gemini pricing page, checked 2 Oct 2026):**
- **Gemini 3.8 Flash** is the latest Flash: $0.75 in / $3.75 out per million tokens until 31 Dec 2026, then
  $1.50 / $7.50.
- The Batch API halves these prices.

Using batch for every offline run, the budget is ≈ **$100** if stage 2 runs before 31 Dec 2026, or ≈ $175 after.
GPU stays at ≈ 55 Kaggle T4-hours.

**Verdict after all three passes:** the project meets every prop.pdf requirement. The novelty is real but narrower
than first claimed, and it is now stated honestly against the two closest papers. Before the TA meeting, the team
should read PolicyGuard and Speculative Interaction Agents in full.
