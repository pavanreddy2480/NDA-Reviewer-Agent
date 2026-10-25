# Test suite rewrite and audit (25 Oct 2026)

The old `tests/` folder was deleted unread and replaced by a suite written from
`docs/proposal/proposal.pdf`, using `src/` only to learn the interfaces. Every test uses tiny
in-code fixtures and a scripted fake model (`tests/conftest.py`), so nothing needs ContractNLI,
a GPU, an API key or the network.

```bash
pip install -e '.[dev]'
pytest -q        # 376 passed, 14 xfailed in about 3 s
pytest -rx       # lists every known problem with its reason
```

## How the suite is organised

| File | Proposal section | What it pins down |
|---|---|---|
| `test_policy_rules.py` | §4 rule base, §1 US jurisdiction | applicability conditions (sandboxed, never executed), deal variables, field constraints, law pack conditions (§16600 only under California law), jurisdiction names |
| `test_retrieval.py` | §4 RAG design | BM25 exact legal terms, dense search, RRF, cross-encoder reranking |
| `test_policy_reviewer.py` | §3 RQ1/H1, §4 Fig. 2, §7 baselines | reverse path finds omissions, forward-only can't, deal filter stops distractors, B4 with and without the filter, facts read from the NDA, same checker for every system |
| `test_checker.py` | §4 Fig. 1 | check label → finding type, and that the reviewer and gold use the same mapping for every rule kind; findings ledger |
| `test_fields.py` | §4 exact comparison of numbers, H1 hidden facts | durations, governing law, min/max rules that interact, template blanks, deal facts inferred from the NDA |
| `test_gold.py` | §6 ground truth without circularity | anchored rules from expert labels, field and term labels, unclear labels unscored (never omissions), applicability on the gold deal, planted overrides |
| `test_planter.py` | §6 planted defects | omissions with gold repairs, violations, distractors, California switch, loopholes, injection changes no gold, split proportions (25% distractor-only, ~50% loophole, 20 injected, 30 state-law) |
| `test_metrics.py` | §7 detection and rigour | both-citations scoring, rule-only score, natural vs planted, false alarms per NDA, bootstrap CIs, paired bootstrap, TOST at 3 points, kappa, ContractNLI macro-F1, fact accuracy |
| `test_repair_scoring.py` | §3 RQ2/H2, §4 Fig. 3, §7 repair loop | redlines, independent judge, fixes and regressions confirmed by a second run, noise floor, per-redline regression rate, validation against expert and human labels |
| `test_tools.py` | §5 tool calling, §9 safety | gated send blocked without approval, request_approval approves nothing, injected errors and recovery, tool P/R vs gold sets, agent following an injection |
| `test_llm.py`, `test_batch.py` | §7 two-stage backbone, §10 cost | cache keyed by the full request, batch mode, Gemini and Claude-agent batch files, cost accounting, data makers from an untested model family |
| `test_labels.py` | §6 two-model labels | disagreements disputed, 20% audit sample, verified labels never overwritten, deals over 3 companies × 4 counterparty types, 3 deal draws |
| `test_packs.py` | §6 packs and law pack | shipped packs meet the spec (~30 rules, ~60% anchored, ~40k tokens, verbatim quotes), the 7 law provisions |
| `test_contractnli_and_rq1.py` | §5/§6 ContractNLI, §7 end to end | 17 checks with 5 held out, the three natural loophole checks, and full `run_rq1` runs on a fake dataset |

Known problems are written as `xfail(strict=True)` tests with the reason. They show up as `x` today;
when someone fixes one, that test starts passing, pytest reports it as a failure, and the marker
should then be removed.

## Things that look inconsistent or fishy

### 1. Proposal vs code: much of the proposed system isn't built yet

- **The RQ2 red-team and repair loop doesn't exist.** There's no opposing-counsel agent, repairer,
  regression checker or loop. Only its scoring (`eval/evaluator.py`) and the redline primitive
  (`Draft.apply`) are there, so the tests cover those.
- **Also missing:** the verifier, the planner, the consistency reviewer, a separate law and risk
  reviewer (law rules are folded into the policy reviewer), the clause parser with obligation
  frames, the QLoRA model, and writes to precedent memory.
- **Most baselines are missing.** B1 long context, B2 naive RAG, B2+checklist, B3 single agent, and
  R1, R1+A and R2 don't exist. The presets are full, no_reverse, no_filter, reverse_only, exhaustive
  and exhaustive_filtered.
- **The cross-reference graph is never used in retrieval.** Rules carry `refs`, and the spec demands
  them, but nothing follows them. "No cross-reference graph" is still listed as an ablation.
- **Dense search and the reranker are wired only into `cc retrieval`.** `cc review` and `cc rq1`
  always run BM25 only. The proposal says retrieval is BM25 + dense + cross-encoder.

I didn't invent interfaces for any of these. Tests for them should be written once their
interfaces exist.

### 2. H1's "fewer checks" can't hold

The full system and B4+filter each make exactly one check per applicable rule, by construction
(`test_full_system_makes_fewer_checks_than_exhaustive_filtered`). The only saving is in segments,
and so tokens, per check (`test_retrieval_shows_fewer_segments_than_exhaustive` passes). The Claude
pilot already saw the same number of checks per NDA. H1 should say "fewer tokens".

### 3. Model-family independence

- The proposal says Claude writes the packs and labels because it is "a model family that no system
  under test, compiler or judge uses". But the only results so far (the 23 Oct pilot) use Claude
  Sonnet as the system under test. `configs/backends.toml` itself warns about this. Those numbers
  can't be reported as results.
- The API-fallback labellers in `[roles]` include `gemini-pro`. That is the compiler and the RQ2
  judge, and the same family as the `gemini-flash` backbone, which the independence rule forbids
  (`test_project_config_fallback_data_makers_are_independent`).

### 4. Steps the proposal says are done that aren't

- All 7 law-pack provisions still have an empty `checked_by` list. The proposal says two teammates
  checked each one against the official text.
- All three packs' `REVIEW.md` checklists are unticked. The proposal says a teammate reviews flagged
  rules, every anchor and a random sample.
- From the project notes (not re-counted here), 287 disputed label keys still wait for a person.

### 5. Code bugs found while writing the tests (each has an xfail test)

1. **Unreadable durations become "absent".** A labelled term such as "until the deal closes"
   normalises to `None`, which means "the NDA does not say". Gold then counts an omission for a
   clause that is there. The same happens inside `autolabel.normalise_answer`, so two labellers who
   both saw the clause agree it's missing. This breaks "unclear labels are never counted as
   omissions". (`test_gold.py`, `test_labels.py`)
2. **The safety metric undercounts.** `send_to_counterparty` without approval but with a missing or
   extra argument is logged as `invalid_args`, not as an attempted unsafe action, because arguments
   are validated before the gate. An injection-following agent can therefore score 0 unsafe
   attempts. `executed_unsafe` is also hard-coded to 0 in `tool_metrics`.
3. **`request_approval` returns no approval id.** So nothing links a human's approval of a request to
   the send it should allow.
4. **The RQ2 judge treats a blanked field as satisfied.** A repairer could "fix" a short term by
   turning it into `____ years`.
5. **Hybrid retrieval ranks zero-score segments.** With an encoder, segments with BM25 score 0 still
   enter rank fusion in index order. The first segments of every NDA get rank credit for matching
   nothing and can outrank the real dense hit.
6. **The ledger's citation union depends on order.** `Ledger.add` merges evidence only when the new
   finding is more confident, so a less confident duplicate's citations are dropped.
7. **"United States" is treated as foreign.** `foreign` is true for `counterparty_country="United
   States"`, because only the codes "US" and "USA" count as domestic.

### 6. Smaller notes (no test)

- `pyproject.toml` says Python ≥ 3.10, but `llm/factory.py` imports `tomllib`, which needs Python
  3.11.
- `Draft.from_text` splits a clause number such as "1." into its own segment, so numbered plain-text
  drafts get one-token segments.
- Field rules in the "exhaustive" presets still use retrieval (k=6) to find the value, so B4 is not
  whole-NDA for field rules. This is fair, because every preset does the same, but it's worth one line
  in the method section.
