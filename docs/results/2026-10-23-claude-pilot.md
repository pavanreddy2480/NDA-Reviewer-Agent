# Claude pilot: RQ1 with Claude Sonnet as the system under test (23 Oct 2026)

Setup: 20 planted test NDAs (the first 20 of `data/planted/test_seed0.json`), the three PolicyNDA packs and the US law
pack, auto labels (`--allow-auto`), deal facts hidden (`--hide-facts`). Claude Sonnet answered every model request through
the new agent backend (`claude-sonnet-agent`: `cc rq1 --batch-queue`, `cc batch export`, agents answer the shards,
`cc batch load`). Script: `scripts/claude_pilot.sh`. Runs: `runs/2026102*-rq1-*-claude-sonnet-agent/`.
About 1,190 distinct model requests (≈1.9M prompt tokens) over 5 rounds.

| System | Precision | Recall | F1 (95% CI) | Omission recall | Violation P / R | Checks per NDA | Prompt tokens |
|---|---|---|---|---|---|---|---|
| Full (two-way, deal filter) | 0.80 | 0.73 | 0.76 (0.70–0.82) | 0.72 | 0.28 / 0.40 | 23.75 | 0.53M |
| Forward only (`no_reverse`) | 0.61 | 0.14 | 0.23 (0.19–0.28) | 0.00 | 0.26 / 0.35 | 20.6 | 0.26M |
| Exhaustive + filter (B4+filter) | 0.82 | 0.73 | 0.77 (0.71–0.82) | 0.72 | 0.31 / 0.40 | 23.75 | 1.08M |

Strict scoring (rule, type and cited evidence must match). Approval-needed and statutory-risk findings are near perfect
(recall 0.91 and 0.92) in the two-way and exhaustive systems.

## What it shows

1. **Reverse retrieval is what finds omissions.** Forward-only finds none of the 159 gold omissions, so its recall is 0.14
   against 0.73. This is the RQ1 ablation, and the gap is far outside the CIs.
2. **Two-way matches exhaustive checking at half the tokens, not with fewer checks.** Recall is identical (0.73) and F1
   differs by 0.01. Both systems make the same number of checks (23.75 per NDA), because the deal filter already removes
   the rules that don't apply and two-way checks every remaining rule once. The saving is prompt size: about 0.53M tokens
   against 1.08M, since each check sees retrieved segments instead of the whole NDA. **H1's "fewer checks" claim should
   become "fewer tokens"** (decision needed).
3. **Deal facts read from the NDA were 100% right** (personal data 14/14, governing law 20/20), so hiding facts cost
   nothing here.
4. **Violations are the weak spot:** precision 0.28 and recall 0.40 in every system. Most false alarms are violations, so
   this is the next thing to look into (gold or prompt).
5. **Prompt injection had no effect.** The 3 injected NDAs score the same as the 17 clean ones (F1 0.77 against 0.76), and
   the answering agents reported ignoring the injected text every time.

## Caveats

- Claude also wrote the packs and the labels, so Claude scores may be flattering; use these numbers for decisions, not as
  the headline. The ratios between systems (the RQ1 question) are less affected than the absolute scores.
- 20 NDAs only, one run, no seeds. Agents answered requests in batches; they were told to judge each request alone, but a
  batch can contain several requests for the same NDA.

## Bug found and fixed on the way

When the planter switched an NDA to California law it only replaced governing-law sentences that its narrow regex
matched. In 15 of the 30 switched NDAs the original clause stayed, so the NDA named two laws while gold said
California. The planter now replaces every operative governing-law sentence (`_LAW_ANY`, test added, 39 tests pass), and
`data/planted/test_seed0.json` was regenerated. Only those NDAs changed.
