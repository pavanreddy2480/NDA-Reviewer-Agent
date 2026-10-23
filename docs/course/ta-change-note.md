# CounselCopilot: changes since the approved proposal

To the TA, from team 2025201049 · 2025201044 · 2025201068 · 2025201038. 22 Oct 2026.

The research questions and system are the same. We audited our method for weaknesses and changed the following.
The updated 5-page proposal is attached.

1. **Jurisdiction is the USA, not India.** Of the 57 ContractNLI test NDAs that name a governing law, about 37 name
   a US state and almost none name India. The law pack now has 7 US provisions: the DTSA notice, SEC Rule 21F-17,
   the Speak Out Act, Cal. B&P §16600 for non-competes and non-solicits, the penalty doctrine and CCPA.
2. **Benchmark data is generated, then checked by people.** The policy packs are written by Claude (rules first,
   prose second) and reviewed by teammates. The NDA labels come from two Claude models labelling independently (95%
   of label keys agree); a person settles each disagreement and audits a sample. Claude is a model family that no
   tested system or judge uses, which avoids circularity.
3. **H1 is sharper.** Forward-only RAG cannot find an omission by construction, so our omission baselines are now
   long context and naive RAG with a checklist. Against exhaustive per-rule checking with the same deal filter, we
   claim equivalent recall (within 3 points, TOST) at fewer checks. We dropped the fixed "≥50% fewer checks". The
   headline setting hides deal facts, so applicability must be inferred from the NDA.
4. **RQ2 scoring.** Gold is exact only for planted defects. Everything else is scored by an independent judge that
   is validated on ContractNLI expert labels and 100 human labels, with fixes and regressions confirmed by a second
   run. We added a baseline that gives one-shot repair the attacker's scenarios, so the loop is not credited for
   that extra information alone.
5. **Smaller scope.** We dropped planted internal inconsistencies and approved-precedent cases. Prompt-injection
   text in 20 NDAs is kept as a safety test.

API costs are now about $60 (about $110 if stage 2 runs after 31 Dec 2026). Compute is unchanged.
