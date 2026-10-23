# CounselCopilot: proposal checked against the brief, plus design risks

> **Historical document.** Kept as a record of its date. The current design is `newdesign.md` (v6; §19 lists the 22 Oct 2026 audit fixes), and the current proposal is `proposal/proposal.tex`.

Written 15 Oct 2026. Compares `proposal/proposal.pdf` (5 pages) with the course brief `prop.pdf`, then lists problems
in the design that will hurt once we run it. Several problems come from looking at the real ContractNLI data while
writing the first code (`code/`); those numbers are measured, not guessed.

## Part 1: does the proposal meet the brief?

**Short answer: yes. Every item the brief asks for is in the proposal.** The gaps are in how some metrics will be
measured (Part 2), not in what is written.

| Brief requirement (prop.pdf) | In our proposal? | Note |
|---|---|---|
| §8 Project title | Yes | |
| §8 Domain and target user | Yes (§1) | |
| §8 Problem statement, 5–8 sentences | Yes, 7 sentences | |
| §8 Research question | Yes, RQ1 + RQ2 | Brief allows "one or two" |
| §7 Hypothesis with a metric | Yes, H1 + H2 with numbers | See problems 3 and 6 on whether the numbers are meaningful |
| §8 Why it matters, what is missing | Yes (§1, §2) | |
| §2 Each capability justified and measured | Yes (§5 table) | Tool calling and reasoning are weaker than they look (problems 4, 5) |
| §8 Architecture, diagram encouraged | Yes, 3 figures | |
| §8 Expected novelty | Yes (§8) | |
| §8 Dataset / evaluation environment | Yes (§6) | See problems 1 and 2 |
| §7 At least one baseline | Yes, B1–B4, R1–R2 | |
| §7 Known ground truth | Yes for detection; overstated for repairs (problem 6) | |
| §7 One metric per capability | Yes | |
| §7 Ablation of each capability the RQs depend on | Yes | |
| §7 Tool-call accuracy and unsafe-action rate | Yes | Unsafe rate is 0 by construction as written (problem 5) |
| §7 LLM judge validated on human labels | Yes, 100 labels, κ | |
| §7 Qualitative examples, failure analysis | Yes (§7 rigour row) | |
| §5 Compute: GPU type/hours, tokens, cost, runs | Yes (§10) | Batch API saving does not apply to the loop (problem 8) |
| §8 Risks and fallbacks | Yes (§11) | |
| §6 Safety plan | Yes (§9) | |
| §6 **"Do not start implementation before your idea is approved"** | **Check** | The TA sent feedback on 9 Oct, but nothing in the project files shows the revised proposal was **approved**. If it hasn't been, the code started today should wait for that, or at least be described to the TA as setup only. |

## Part 2: problems in the design, most serious first

### 1. ContractNLI NDAs are not Indian NDAs (measured)
> **Update 16 Oct 2026:** resolved by switching the jurisdiction to the USA (newdesign.md §17).
- Only **3 of the 123 test NDAs mention India at all.** Of those with a governing-law clause, almost all are US
  states, England, South Africa or Canada.
- **Consequence A:** a rule like "governing law must be India unless the GC approves" fires on nearly every NDA. That
  one rule will dominate the violation counts and make every system look similar.
- **Consequence B:** the India law pack (ICA s.27, s.28) only bites when Indian law governs the contract. Flagging
  s.27 on a California-law NDA is legally wrong, so the law reviewer will mostly produce findings that shouldn't
  exist, or none at all.
- **Fix:** in the deal context, say the company is Indian but the governing law is whatever the NDA says. Make the
  law reviewer conditional on Indian governing law, and plant Indian governing law plus s.27/s.28 risks in a
  controlled subset (say 40 NDAs). State in the paper that natural NDAs are mostly foreign-law. Alternatively, drop
  "India only" for the policy part and keep India only for the law pack.

### 2. Half the NDAs are templates, and half are mutual (measured)
- About **60 of 123 test NDAs contain blanks** (`______`, `……`), and about **58 are mutual**.
- Blanks break field rules: "the confidentiality term is ____ years" has no value, so it is neither compliant nor
  an omission.
- Mutual NDAs make "loophole from the company's side" undefined unless someone records which party the company is.
- **Fix:** add two hand-labelled fields per NDA: `is_template` and `company_party` (which named party we are). Field
  rules on blank fields are scored as "unscored", not omissions. Do this in the same pass as the field-rule labels.

### 3. H1's "≥50% fewer checks" is decided by whoever writes the policy packs
- In the design, two-way retrieval checks every **applicable** rule once, and B4 checks **every** rule. So "50% fewer
  checks" is true exactly when fewer than half the rules apply to a typical deal. That depends on how the policy
  authors spread the `applies_if` conditions, not on our method. A TA can call it circular.
- The same problem hits distractors. Our system reads applicability from the deal form, so it ignores distractors
  automatically, while B4 has no filter and always flags them. That win is guaranteed by construction.
- **Fix:**
  - Fix the share of deal-specific rules in advance and give it to the pack authors as a written spec (e.g. "about
    40% of rules apply to only one counterparty type"). Report checks as a share of applicable rules.
  - Add a fairer baseline, **B4+filter** (exhaustive checking with the deal filter). Then the honest RQ1 claims are
    (a) reverse retrieval vs forward, and (b) retrieval vs reading the whole NDA per rule, at equal applicability.
  - Make some applicability facts **implicit in the NDA text** rather than in the form (e.g. whether personal data is
    shared, whether the counterparty is a vendor). Only then is applicability a reasoning step rather than a
    lookup.

### 4. "Reasoning" on applicability is a boolean lookup as designed
- The proposal measures "accuracy of every intermediate applicability decision". But `applies_if` is evaluated
  deterministically from the form (in the code it is a safe boolean expression), so its accuracy is 100% by
  construction.
- The real reasoning sits in two other places: the **policy compiler** (turning prose into the right condition) and
  facts that are implicit in the NDA (problem 3).
- **Fix:** measure applicability accuracy at those two points: compiled condition vs gold condition, and inferred deal
  facts vs gold. Say that clearly in the reasoning row.

### 5. Tool calling is mostly scripted, so tool-call accuracy could be trivial
- In the current architecture (and in the first code), retrieval and checks are called by Python, not chosen by the
  model. If the pipeline always calls the same tools in the same order, "tool selection precision" is 100% and
  meaningless.
- `send_to_counterparty` is blocked by the harness, so the **unsafe-action rate is 0 by construction** too.
- **Fix:**
  - Give the reviewers and the repairer a real tool-calling loop for the parts that need choices (approval matrix,
    statute lookup, cross-reference resolution, `request_approval`), and keep fixed code only for the core checks.
  - Report the **attempted** unsafe-action rate (the model tried to call a gated tool without approval, including
    under prompt injection), not only executed actions.
  - Note that Llama-3.1-8B is weak at multi-step tool calling. Budget for constrained JSON decoding from day one,
    not as a fallback.

### 6. RQ2 ground truth is less "exact" than the proposal says
- "The original clause is the gold repair" only works if the original clause satisfies **our** synthetic policy.
  Often it won't: if we plant "2 years" over an original "3 years" but the policy needs 5 years, restoring the
  original is still a violation.
- Natural defects have no original clause, and gold frames exist for only 40 NDAs.
- "Remaining defects", "regression rate" and "repair success" all require checking an **edited** draft that has no
  ContractNLI labels. Something has to do that checking. If it's our own checker, the loop can game it (as the
  proposal admits). If it's a separate model, that model is an LLM judge and needs its own human validation.
- The "5 held-out ContractNLI checks" don't solve this: on an edited draft they still need a model to answer them.
- **Fix:**
  - Gold repair = "the edited clause satisfies the rule and keeps the original obligation frame where the rule allows
    it", not literal equality.
  - Plant defects only where the original clause satisfies the pack (check this when planting).
  - Use **one independent evaluator**: a stronger model that the loop never sees (Gemini Pro), validated against human
    labels on about 100 (rule, edited draft) pairs. Report its agreement next to every RQ2 number.
  - The "blind acceptance by teammates" is not blind, because teammates built the system. Use classmates outside the
    team, or call it "acceptance by non-author raters".

### 7. Planting defects into ContractNLI changes other labels
- One ContractNLI span is often evidence for several hypotheses. Deleting the return clause to plant an omission can
  also remove evidence for "permissible post-agreement possession" (nda-20) or "survival" (nda-19). Then the
  expert labels for those checks are wrong for the planted copy.
- Deleting clauses also breaks cross-references ("as set out in Section 7"), which creates accidental inconsistency
  defects.
- Only some hypotheses ever appear as natural violations. In the test set, nda-8, 10, 11, 12, 13, 15 and 18 have
  **zero** Contradiction labels. So `require` rules anchored to them can only produce natural omissions, and natural
  violations come mostly from nda-2, nda-7, nda-17 and nda-20.
- **Fix:** the planter must re-derive the gold status of every anchored rule whose evidence spans it touched (mark them
  unscored if unclear), and log removed cross-references. Report natural violations as a small, separate category.

### 8. The Batch API discount mostly doesn't apply to agents
- The cost plan assumes everything on Gemini runs through the Batch API at half price. The batch service returns
  results asynchronously, up to a day later. The RQ2 loop is sequential (attacker, repairer, checker, up to 3
  rounds), and the detection pipeline has stages (planner, reviewers, verifier).
- **Fix:** run in stage-synchronous batches: one batch per stage across all NDAs, then the next stage. This works,
  but needs a batching layer in the code and several days of wall-clock time for the loop. Alternatively, run the
  loop on the normal API at full price. That roughly doubles the RQ2 line (≈ $13 → ≈ $26 before Jan 2027). Still
  inside budget.
- The verifier runs "Flash with thinking on". Thinking tokens are billed as output, which the $15–22 estimates don't
  include. Cap the thinking budget and add it to the estimate.

### 9. Fairness: the tuned model sits inside "Full" only
- The proposal says every system in a comparison uses the same backbone. But Full uses the QLoRA model for checks,
  while B2/B4 use the prompted backbone. Any win over B4 could then come from fine-tuning, not from retrieval.
- **Fix:** run B4 with the same tuned checker (or run Full with the untuned one) for the RQ1 headline. The
  "no reverse" ablation is already clean.

### 10. "2 seeds" on Llama at temperature 0
- At temperature 0, vLLM gives almost the same output for both seeds, so the second seed adds almost no variance
  information.
- **Fix:** either sample at temperature 0.3–0.7 for the seed runs, or replace seeds with bootstrap CIs over NDAs plus
  two different deal-context draws (we already generate deal contexts from a seed).

### 11. Retrieval recall caps omission precision (measured)
- With BM25 alone, the gold evidence span is in the top 8 retrieved segments only **80%** of the time on dev (88% at
  12, 95% at 20). A clause that isn't retrieved looks missing, so the reverse path will report false omissions there.
- NDAs are short (about 84 segments, ~3k tokens on average), so "whole NDA per rule" (B4) easily fits even on Llama.
  B4 is therefore a strong competitor on omission recall. Expect it to win on recall and lose on cost.
- **Fix:** already partly in the code (k=12, neighbouring segments added). Measure dense + rerank early on dev. If
  recall stays below about 95%, frame H1 around cost at equal recall, which is what the "within 3 points of B4"
  clause already says.

### Smaller points
- **Model names and prices.** "Gemini 3.8 Flash" prices were checked on 2 Oct. Re-check them right before stage 2.
- **Kaggle quota is per person.** Four teammates have four 30 h/week quotas, so GPU time is less tight than §10
  suggests. Mention it as slack.
- **Law pack wording.** Indian courts have upheld some employee non-solicitation clauses as not being restraints of
  trade. Keep s.27 findings to non-compete clauses and word non-solicit as "possible risk".
- **DPDP Act.** Its rules were notified in Nov 2025 with phased commencement. Date the law pack and say which duties
  are in force.

## What I'd change, in order
1. Confirm the TA approved the revised proposal (brief §6).
2. Agree a written spec for the policy packs (share of deal-specific rules, implicit deal facts, India governing law
   only where planted), so the pack authors can start.
3. Add hand-label fields `is_template`, `company_party` and `governing_law` to the field-labelling pass.
4. Add the B4+filter baseline, and a "same tuned checker" rule for B4.
5. Choose the independent RQ2 evaluator (Gemini Pro plus human validation) now, before the loop exists.
6. Budget RQ2 on the normal API, or build stage-synchronous batching.

None of these needs a proposal rewrite. Items 3, 4 and 6 go into the code. Items 1, 2 and 5 are team decisions.
