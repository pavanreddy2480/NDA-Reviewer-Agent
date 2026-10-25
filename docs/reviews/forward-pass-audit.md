# Audit of the review forward pass (25 Oct 2026)

Pavan asked for an end-to-end check of one review, looking for logic that is invented,
arbitrary or inconsistent, like the deal problems in [gold-deals-audit.md](gold-deals-audit.md).
I followed one RQ1 run from the command line to the metrics: `scripts/claude_pilot.sh` →
`cli rq1` → `experiments/rq1.py` → `PolicyReviewer.review` (`review/deal_facts.py`,
`review/policy_reviewer.py`, `review/checker.py`, `review/fields.py`) → `gold_for` and
`score_detection`.

Each point was reproduced on the shipped packs, ContractNLI or a small fixture. Points marked
*(test)* have a test in `tests/test_forward_pass.py`: a strict xfail for a bug, a passing test
for behaviour that is documented but not wrong on its own. Nothing in `src/` was changed.

**Verdict.** The plumbing works: each preset does what its docstring says, checks are cached,
seeded and sent to one checker model, and failed checks are counted rather than reported. The
problems are in what the system is given, and in facts it reads more than once. The biggest one
is point 1: RQ1 currently hands the reviewer the answer key's rule list, so it measures the
checker, not the system the proposal describes.

## Status

Fixed on 25 Oct, with Pavan's go-ahead:
- **Point 2.** Each field is read once per review. When governing law is read from the NDA
  for applicability, the governing-law field rule reuses that reading. A law written on the form
  is a deal fact, so the clause itself is still read for the field rule.
- **Point 3.** A rule whose applicability depends on a fact that is still unknown is checked,
  not dropped. That covers an unreadable personal-data reply and an NDA with no governing law.
  Such rules are listed in `ReviewResult.undecided_rules`, and in the `rq1` rows.
  `applicability()` moved to `policy/schema.py` so that gold and the reviewer share it.
- **Point 4, B4 half.** Exhaustive presets now extract fields from the whole NDA. The
  forward-only half is still open.
- **Planted manifests.** `data/planted/test_seed0.json` was re-planted with the new deals:
  - same 264 defects in 123 NDAs
  - partner 62, vendor 24, customer 20, employee 17
  - 12 foreign counterparties (was 33), 25 with personal data unknown

- **Point 1.** Policy compiler built (requirement cards, model-judged applicability; design §20).
  RQ1 now scores compiled cards against the gold lists; runs without `--gold-pack` are labelled
  `oracle_rules`. No compiled packs exist yet (needs a model run: `scripts/claude_pilot.sh`).

Still open: points 5 to 8 and the runner items.

## Severe

### 1. The reviewer is given the gold rules, and the anchored rules are ContractNLI's own questions

- `scripts/claude_pilot.sh` passes `packs/policynda/*/gold_rules.yaml` as `--pack`. Each file
  starts with "GOLD rule list ... Keep away from the reviewer builders: used only to score the
  policy compiler (design D17)". D17 says the main results use *auto-compiled* rules. No policy
  compiler exists in `src/` (proposal §4: "a policy compiler turns each company's prose policies
  into a rule base"). The prose policies are in `packs/policynda/*/policies/` and nothing reads
  them.
- 53 of the 90 rules are anchored to a ContractNLI hypothesis. For 51 of the 53, the rule's
  `term`, which is the exact statement the checker gets, matches the hypothesis text at 90% or
  more (difflib ratio). So the checker is asked ContractNLI's question word for word, and gold
  is ContractNLI's answer to that question. The keywords used for retrieval were written by the
  pack generator that also wrote the gold.
- Effect: RQ1 numbers on these rules measure prompted NLI on ContractNLI, with oracle rules,
  oracle wording and oracle retrieval hints. B1 (long context) gets the prose pack, so the
  comparison isn't like for like. Once the QLoRA model is tuned on 12 of the 17 hypotheses
  (D18), the tuned checker sees its own training questions on those rules.

**Fix:** build the compiler (prose → rules), run RQ1 on compiled rules, and report the
gold-rule run as an oracle upper bound. Score the compiler separately against `gold_rules.yaml`,
as D17 intends. At least report anchored rules on held-out hypotheses apart from the rest.

### 2. Governing law is read twice, and the two readings can disagree *(test)*

`resolve_deal` asks the backbone (`self.llm`) for governing law, to decide which rules apply. The
governing-law field rule (saas P-22, hospital P-24, manufacturer P-21) asks the checker
(`checker_llm`) the same question again. With two different models, or one model at
temperature > 0, the deal can say California, which switches on the §16600 rule, while P-22 judged
"Delaware" and found nothing wrong. That gives one review with two governing laws.

The same happens on the form side. A governing law written on the form is used for applicability,
but the field rule ignores it and reads the NDA again.

**Fix:** read each fact once per review and pass the value (with its evidence) to the field
rule. The `rq1` row already logs `inferred_facts`, so the field check can reuse that value.

### 3. An unknown personal-data fact silently means "no personal data" *(test)*

- If the personal-data reply is malformed, `resolve_deal` stores `None`. Conditions evaluate
  `None` as false, so every `personal_data` rule leaves the review and every `not personal_data`
  rule joins it. That happens with no record of it, except a `None` in `inferred_facts`.
- If BM25 finds no segment for the personal-data query, `infer_personal_data` returns `False` without
  asking the model.
- Gold treats an unknown fact as unscored, so these rules drop out of the denominator rather than
  counting as misses. The hide-facts run, which is the H1 setting, then scores fewer rules
  without saying so.

**Fix:** keep unknown as unknown. Check rules whose applicability depends on an unknown fact
(conservative), or list them as undecided in the result and report how many there were.

## Moderate: these make the comparisons unclean

### 4. B4 and the "clean" ablation still retrieve for field rules *(test)*

Field rules call `extract_field`, which always uses a fixed BM25 query and the top 6 segments, in
every preset:

- B4 is described as "whole NDA in the prompt". That holds for term rules, but its field rules
  (7 or 8 of the 30 rules in each pack) still see only 6 retrieved segments.
- The no-reverse ablation is described as "the clean RQ1 test". It still runs a rule-to-segment
  search for every field rule, so field violations are found by reverse retrieval in a
  forward-only system. Only field omissions are dropped.

**Fix:** in exhaustive presets, extract fields from the whole NDA. In forward-only presets,
extract fields only from segments the forward path hit.

### 5. In two-way mode the forward path can't add a rule, only segments

With the deal filter on, the reverse path already checks every applicable rule. A forward hit
only adds its segments to that rule's single check (`direction="two_way"`). I measured this on 40
dev NDAs: forward added segments to 24% of checks, 4.7 segments on average (saas 211/880,
hospital 213/920). So "full vs reverse_only" measures a bigger context window, not violations
the reverse path missed.

The forward cut-off `forward_min_score = 4.0` is a raw BM25 score. Its value depends on the size
of the rule index and the length of the query, nobody calibrated it, and it is ignored once an
encoder is used.

**Fix:** describe the forward path as extra recall context in the write-up. Calibrate the
cut-off on dev (forward-hit precision against gold evidence), or use rank only.

### 6. Some findings get no model call, and their confidences are fixed numbers *(test)*

- A require rule whose query matches no segment becomes an omission at confidence **1.0** without
  a model call, and still counts as one check (`run_check` with empty ids).
- Field findings carry fixed confidences: 0.6 for "not found" and 0.8 for a value.
- `Ledger` keeps the finding with the highest confidence, and the cost plan's cascade sends
  "unsure" checks to Gemini. Neither works with numbers that aren't comparable: model confidences
  sit next to constants.

**Fix:** mark these findings with `confidence=None` or `source="rule"`, and leave them out of
calibration and of the cascade's confidence threshold.

### 7. Check counts mix model calls, cached repeats and no-call checks

`n_checks` counts each field rule separately, even when two rules read the same field (P-04/P-06
in the fixture, the ≥/≤ survival pairs in the packs; the second read is a cache hit). It also
counts the no-call omissions above. H1's "fewer checks" claim is already impossible by
construction (see the `test_full_system_makes_fewer_checks_than_exhaustive_filtered` xfail), and
these counts make the number harder to read. **Fix:** report model calls, input tokens and checks
separately.

### 8. No verifier

Proposal §4 and Figure 1: "the verifier keeps a finding only if both citations support it", and
"no verifier" is a listed ablation. Today every finding from a check goes straight to the ledger.
The verifier ablation and the "verifier precision" metric can't be run yet.

## Runner (`experiments/rq1.py`, `cli rq1`)

- **Labels dropped silently.** Without `--allow-auto`, `load_labels` drops every auto label.
  That leaves `labels` empty for most NDAs, so every field rule and unanchored rule is unscored
  and only anchored rules count. Nothing in the metrics says so. **Fix:** warn, and write
  `n_scored_rules` by kind into `metrics.json`.
- **Pending NDAs change the subset.** NDAs whose checks are still in the batch queue are
  skipped, and metrics are computed over the rest. Two presets compared on different rounds can
  cover different NDAs. **Fix:** refuse to write final metrics while `pending_batch_ndas > 0`, or
  score only the intersection.
- **`--limit` is applied before the planted filter.** You get the planted NDAs among the first
  N of the split, not N planted NDAs.
- **The injection metric is unpaired.** It compares recall on the NDAs with injected text
  against recall on the other NDAs, which are different documents (about 20 in the pilot). The
  same NDA with and without the injection would isolate the effect.
- **Planted manifests were stale (re-planted 25 Oct).** The planter saves each deal in its manifest, and `rq1` uses
  that deal. In `data/planted/test_seed0.json`, 115 of 123 deals differ from what the current
  `deals.py` gives, so planted runs still use the old round-robin deals, with invented employees
  and foreign counterparties. **Fix:** re-plant (`cc plant ...`) after the counterparty labels
  are merged.

## Checked and fine

- Every preset sends all checks to `checker_llm`. Field rules go there too.
- Cache keys include temperature and seed, so seed runs really vary.
- Failed checks give no finding and are counted under `check_errors`.
- A forward-only system cannot report an omission, field omissions included.
- `applicable_rules` uses the completed deal and is the same for every preset.
- Context length: the longest test NDA is about 10.4k tokens (median 2.4k), so B4 fits in a
  16k-context Llama.

## Suggested order

1. Point 1: a compiler, or at least an honest label on the oracle-rules run. This changes what
   RQ1 measures.
2. Points 2 and 3: read each fact once, and keep unknown as unknown.
3. Re-plant with the new deals, and make the runner warn about dropped labels and pending NDAs.
4. Points 4 to 7 before the ablation table is written.
