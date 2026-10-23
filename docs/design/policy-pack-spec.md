# Policy pack spec

Written 15 Oct 2026 for teammates writing the packs by hand; since 16 Oct 2026 the packs are generated to this spec
(next section) and teammates review them. Reviewers must not be the people building the reviewer (design D17). The spec is fixed in advance, so the benchmark can't be shaped to fit the method
(review problem 3).

## Written by Claude agents (23 Oct 2026)
The three packs in `packs/policynda/` were written by Claude Sonnet agents to this spec, cross-checked by Claude
Haiku and imported with `cc packs import`. Labels were made the same way (`cc labels import`). The API path below
remains as a fallback.

## Generated instead of hand-written (16 Oct 2026)
The packs are now written by an LLM (`cc packs generate`, src/counselcopilot/benchmark/packgen.py) to this
same spec. The rule list is written first and checked against the targets below; the prose is then written from the rules
and must quote each rule verbatim; a second model cross-checks each quote. A teammate then works through each
pack's `REVIEW.md`: flagged rules, missing quotes, a random spot check and a read-through. That takes about 2 h per pack. The generator
must be a model family that no backbone, the compiler or the RQ2 judge uses (`[roles]` in `configs/backends.toml`;
`cc packs generate` refuses otherwise; default Qwen-72B on Together), and the reviewer builders never see the
generator's prompts. Audit additions (22 Oct 2026) are in the table below and in `check_spec`.
The sections below remain the spec.

## What each pack contains
1. **Policy prose:** about 40k tokens of realistic company policy documents (vendor management, data protection,
   IP, legal approvals, HR). NDA rules are buried in it, as in a real company. Model the style on public corporate
   policies.
2. **Gold rule list** in `packs/<company>/gold_rules.yaml`, in the format of `packs/toy/toy_pack.yaml`. It is
   kept away from the reviewer builders and used only to score the policy compiler and as the hand-checked
   ablation.

## Rules per pack: about 30, with this mix
| Property | Target | Why |
|---|---|---|
| Anchored to a ContractNLI hypothesis (`anchor:`) | about 60% (18) | Real NDAs then come with expert-labelled natural defects |
| Field rules (term length, governing law, return deadline) | about 25% (7) | Labelled per NDA by two models, disagreements settled by a person |
| Other (needs hand labels or planting only) | about 15% | |
| **Applies to only some deals** (`applies_if` not `True`) | **40% ± 5%** | Fixed in advance, so "fewer checks" is not tuned to win |
| Conditions that use `personal_data`, `governing_law` or `us_law` | at least 5 | These facts are hidden from the form in the `--hide-facts` runs, so applicability has to be read from the NDA |
| `forbid` rules | at least 4 | Violations need something to forbid |
| Rules with an approval route (`approval:`) | 3 to 5 | Approval-needed deviations and precedent memory |
| Rules with cross-references (`refs:`) | at least 5 | Tests the cross-reference graph |
| Governing-law rules | **at most 1**, approval-gated | Most ContractNLI NDAs are US-law, so this rule fires almost everywhere; reported separately |
| Numbers in anchored rules | **none** | The ContractNLI label can't check a number ("return within 30 days" anchored to nda-16 would mark a 90-day NDA compliant). Numbers go in field rules |
| Min/max pairs on one field (`>=` and `<=`) | at least 3 | RQ2's interacting fixes: fixing one can break the other |
| Refs to a rule in another policy document | at least 3 | Compilation must join documents, not copy one quote |
| Conditional `forbid` rules anchored to nda-2, 12, 18 or 20 | at least 3 | The planter has clauses for these; without them distractor-only NDAs get no distractor |
| Conditions | only deal variables | `check_spec` evaluates every condition on sample deals |

**Anchoring tip:** these hypotheses have natural violations (Contradiction labels) in the test set: nda-1, nda-2,
nda-7, nda-17, nda-20. These have none: nda-8, 10, 11, 12, 13, 15, 18. A `require` rule anchored to the second group
can only ever produce natural omissions.

## Three US companies, deliberately different
- A SaaS firm: vendor-heavy, personal data common.
- A hospital group: personal data always, strict HIPAA and CCPA rules.
- A manufacturer: IP-heavy, partners and employees, little personal data.

## NDA labels (two models, then a person)
Run `cc labels auto --split test` (and `--split dev`): Qwen-72B and Gemini Pro label every NDA. A person settles
every disagreement (`disputed`) and checks the 20% audit sample, then sets `verified: true`; `cc labels accuracy`
reports the accuracy of agreed labels. (`cc labels init` still pre-fills entries for fully manual labelling.) Fields to label per NDA:
- `is_template`
- `mutual`
- `company_party` (which named party is our company)
- `governing_law`
- `personal_data`
- the field-rule values (use `blank` where a template leaves a value empty)

Report the audited accuracy (`cc labels accuracy`).

## Law pack
`packs/law/us_law_pack.yaml` is a **draft** (the jurisdiction is the USA since 16 Oct 2026; the India pack is in `packs/law/archive/`). Each provision needs two teammates to check it against the
official text and add their names to `checked_by`. The code warns until every provision has two names.
