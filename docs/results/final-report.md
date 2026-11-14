# CounselCopilot: final project report (14 Nov 2026)

Status: **every component in the proposal is built and tested end to end; the real-model runs
are still to do.** All numbers below the pilot section come from an offline plumbing check on
synthetic data and must not be reported as results.

## 1. Problem

A consultant drafts an NDA for a new deal. Before it goes out, it must be checked against the
company's own policies (which rules apply depends on the deal: counterparty type, personal data,
governing law) and against US law. Two things go wrong in practice: required clauses are
*missing* (omissions, which forward clause-by-clause review cannot see), and the counterparty
later *exploits* wording that technically passes review (loopholes). CounselCopilot targets both:

- **RQ1:** does applicability-aware, two-way retrieval (clause → rule *and* applicable rule →
  NDA) find more defects, especially omissions, than long context, naive RAG and a single agent?
- **RQ2:** does a red-team and repair loop (opposing counsel attacks, repairer redlines, full
  re-check catches regressions) leave fewer problems than one-shot repair and self-refine?

## 2. Related work (summary; full notes in docs/reviews/)

PolicyGuard (arXiv 2606.32004) checks documents against policy with retrieval, but forward only
and without deal applicability ([TA feedback](../reviews/ta-feedback-policyguard.md)). NOMOS has
no overlap ([comparison](../reviews/nomos-comparison.md)). ContractNLI gives span-level NDA
entailment labels; CUAD gives clause-type labels; Self-Refine is the R2 baseline. The
[novelty check](../reviews/novelty-check.md) lists the rest.

## 3. Method (what is built)

| Part (proposal) | Code |
|---|---|
| Policy compiler: prose → requirement cards, model-judged applicability | `policy/compiler.py`, `cc compile` |
| Planner (chooses reviewers; never drops the policy reviewer) | `agents/planner.py` |
| Two-way policy reviewer, deal filter, presets | `review/policy_reviewer.py` |
| Obligation frames (prompted, regex fallback; fine-tune target) | `review/frames.py` |
| Cross-reference graph (one-hop expansion, inherited approvers) | `review/xref.py` |
| Law reviewer and dispute-risk checks | `review/law_reviewer.py` |
| Consistency reviewer (defined terms, cross-refs, dates) | `review/consistency.py` |
| Verifier (structural + model verdict) | `review/verifier.py` |
| Approval desk on the gated tool registry, precedent memory | `agents/handoff.py`, `agents/memory.py`, `tools/` |
| Full pipeline and its 11 ablations | `agents/pipeline.py`, `cc pipeline`, `cc rq1 --system pipeline --ablation X` |
| Baselines B1 long context, B2 naive RAG, B2+checklist, B3 single agent, B4 exhaustive | `baselines/systems.py`, `cc rq1 --system b1/b2/b2_checklist/b3`, `--preset exhaustive*` |
| Opposing counsel, repairer, regression checker, loop; R1, R1+A, R2 | `repair/`, `experiments/rq2.py`, `cc rq2` |
| Independent evaluator, H2 paired ratio, blind acceptance sheet and kappa | `eval/evaluator.py`, `experiments/rq2.py`, `cc rq2-kappa` |
| Local-first cost cascade (calibration, threshold on dev) | `experiments/cascade.py`, `cc cascade` |
| Policy-size sweep (padded corpora) | `experiments/sweep.py`, `cc sweep` |
| QLoRA multi-task fine-tune (NLI on 12 hypotheses, CUAD, frames) | `finetune/`, `cc frames`, `cc finetune`, [guide](../guides/qlora-kaggle.md) |
| PolicyNDA benchmark: gold, deals, planter, labels, 3 packs, US law pack | `benchmark/`, `packs/`, `data/` |
| Offline backend and smoke run of every experiment | `llm/heuristic.py`, `benchmark/synthetic.py`, `cc smoke` |

Design decisions taken while building are in [design.md §21](../design/design.md).

## 4. Experiments (how to run them)

```bash
cc rq1 --system reviewer --preset full|no_reverse|exhaustive_filtered ... --hide-facts   # RQ1 core
cc rq1 --system pipeline --ablation full|no_frames|no_xref|no_verifier|...                # ablations
cc rq1 --system b1|b2|b2_checklist|b3 ...                                                 # baselines
cc compare runs/A runs/B                                                                  # paired CIs
cc sweep --padding <public policy dirs>; cc compile ...; cc rq1 ...                       # H1 size trend
cc rq2 --pack ... --planted data/planted/test_seed0.json --limit 40 --evaluator-backend gemini-pro
cc rq2 --acceptance-sheet runs/<rq2>/repairs.jsonl; cc rq2-kappa A.csv B.csv key.json      # blind review
cc cascade runs/<llama> runs/<gemini> --pack ...                                          # cost ablation
cc report runs/*                                                                          # one table
```

Every model runs first on Llama (Kaggle vLLM, [guide](../guides/kaggle-vllm.md)) and is then
confirmed on Gemini Flash. The RQ2 evaluator must be a model family no repair system uses; the
runner refuses otherwise.

## 5. Results so far

**Claude pilot (23 Oct, 20 planted NDAs, [write-up](2026-10-23-claude-pilot.md)).** Full two-way
review: F1 0.76, omission recall 0.72. Forward only: F1 0.23, omission recall 0.00. Exhaustive
with the deal filter: F1 0.77, at twice the prompt tokens. Claude also wrote the packs and labels,
so these are for decisions, not headlines.

**Smoke run (14 Nov, synthetic, offline heuristic backend).** All 11 RQ1 systems and ablations,
a planted pipeline run, all 7 RQ2 systems, the cascade and the acceptance sheet run to
completion and write metrics (`cc smoke`). The heuristic model is a keyword matcher, so the
numbers only show that each path produces scored output. In particular the baselines score 0
because the heuristic does not answer their free-form prompts.

**Tests:** 517 pass; 4 strict xfails mark human tasks (below).

## 6. Decisions and open items for the team

1. **H1 wording.** The pilot shows two-way review makes the *same number* of checks as
   exhaustive-with-filter (the filter already removes inapplicable rules) but uses about half
   the tokens. The proposal says "fewer checks"; the test suite now checks "fewer tokens". The
   proposal text should change to match (needs the team's agreement and the TA note).
2. **Human tasks (strict xfails):** each pack's `REVIEW.md` checklist (saas, hospital,
   manufacturer), and two teammates checking each provision of `packs/law/us_law_pack.yaml`
   against `us_law_sources.md`. Also the 55 disputed label keys in `data/labels/ndas_auto.yaml`.
3. **Real runs:** RQ1 test split on Llama then Gemini Flash; the sweep; RQ2 on 40 NDAs; the
   cascade; two QLoRA seeds; the blind acceptance review by two teammates who did not build the
   loop.
4. **Send the TA** `docs/course/ta-change-note.md`.

## 7. Limitations

- Packs, labels and planted defects are model-written (Claude, Qwen); human review is pending.
- Gold for natural defects covers only rules anchored to ContractNLI hypotheses.
- Obligation frames and the consistency checks use regexes as fallbacks; they are tuned to
  US-style NDAs.
- The loop's "conflict" stop only detects min/max field clashes and fixed-then-broken rules, not
  every pair of rules that pull a clause in opposite directions.

## 8. Future work

Learned applicability from precedents; using the tuned adapter as the attacker; repair of
multi-clause defects as one edit; a real (not padded) large policy corpus for the size sweep.
