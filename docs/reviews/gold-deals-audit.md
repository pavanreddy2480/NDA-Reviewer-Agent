# Logic audit of gold.py, deals.py and related files (25 Oct 2026)

Pavan asked for a check of `benchmark/gold.py` and `benchmark/deals.py`. I followed the logic
into the files they depend on and that depend on them: `planter.py`, `autolabel.py`,
`review/fields.py`, `experiments/rq1.py`, and the three shipped packs.

Each problem below was reproduced on the shipped packs, the shipped label file
(`data/labels/ndas_auto.yaml`, 184 NDAs) or a small fixture. The ones marked *(test)* now have a
strict-xfail test in `tests/`. Fixes are suggested but not made.

**Verdict.** The core of gold.py works as designed: anchored rules take the ContractNLI expert
label, applicability is judged on the gold deal, unknown facts make a rule unscored, and planted
overrides win over natural labels. The problems are in four places: how field rules treat a
missing value, how deals are drawn, what the planter doesn't track, and rules in the packs that
point the wrong way or duplicate each other. Several of them inflate the gold omission count, so
they also inflate the main H1 number (omission recall).

## Status

Points 4, 5, 6 and 8 are fixed (25 Oct, Pavan's go-ahead):
- `deals.py` now reads the counterparty type and country from new label keys (`counterparty_kind`,
  `counterparty_role`, `counterparty_country`), labelled by two agents, with disagreements disputed.
- A country the NDA doesn't state is the US; no foreign counterparty is invented.
- Unknown personal data stays blank on the form.
- Company, value band and any role the NDA doesn't show are drawn from a seed per NDA id.
- `deal_sources` records which facts were read and which were assigned. `rq1` writes it to every
  review row.

Points 1, 2 and 3 are fixed (25 Oct, Pavan's go-ahead), in both gold and the reviewer:
- **Point 1.** An NDA without the clause is judged on what that absence means
  (`FieldConstraint.check_absent`). No restriction lasts 0 months, so "at most" rules on the term,
  survival and non-solicit are met. No deadline never ends, so "return within 30 days" is still
  an omission, while "at least 10 days" is met. A missing law only meets "not in" rules.
- **Point 2.** A value given without a number is now "unspecified" and unscored. The extractor and
  the labellers are told to answer "unspecified". In the existing labels, null return deadlines
  are taken as "unspecified" whenever ContractNLI's expert label for nda-16 says the NDA has a
  return clause.
- **Point 3.** The planter reads the clause topic of unanchored pack forbid rules from their
  title and term: saas P-09 and P-24, hospital P-25 and P-26, manufacturer P-18. It no longer
  plants a clause that would break one of them unrecorded, and it can plant violations of them.
- **Effect on the test split** (123 NDAs, natural gold, hidden facts): field omissions went from
  323 to 155, and all natural omissions from 887 to 719. `data/planted/test_seed0.json` was
  re-planted (265 defects). The merged counterparty labels (25 Oct, 184 NDAs, 55 disputed keys) are in `data/labels/ndas_auto.yaml`; planted manifests still hold the old deals and must be re-planted (forward-pass-audit.md).

## Severe: these change the headline numbers

### 1. Every missing field becomes an omission, even for "at most" rules *(test)*

In `gold.py`, `field_value` returns `(True, None)` when a label says a field is absent, and
`gold_for` turns that into an omission whatever the rule says. `review/fields.py` does the same on
the system side. That is right for a minimum ("term at least 24 months"). It is wrong for a
maximum: an NDA with no non-solicit clause satisfies "non-solicit at most 12 months".

How often this bites, from the shipped labels:

| Field | Labelled absent |
|---|---|
| `return_deadline_days` | 149 of 184 NDAs |
| `non_solicit_months` | 146 of 184 NDAs |
| `survival_months` | 92 of 184 NDAs |
| `confidentiality_term_months` | 31 of 184 NDAs |

The rules this hits include saas P-11 (≤60), P-23 (non-solicit ≤12) and P-30 (≤84); hospital
P-08 and P-23; and manufacturer P-19 and P-20. One missing survival clause gives two omissions,
one for the ≥ rule and one for the ≤ rule.

Because the reviewer makes the same mistake, these "omissions" are found almost for free: the
field extractor says null, so the system reports an omission. That makes omission recall look
better than retrieval earns.

**Fix:** a missing value satisfies `<=` and `!=`/`not in` rules. Only `>=`, `==` and `in` rules
make an omission. Apply the same rule in `check_field_rule`.

### 2. "Promptly" and other unreadable values are treated as "absent"

This is the bug from the first audit, but its size is now clear. Most return clauses say
"promptly upon request" and have no number. Labellers answer with text, `_normalise` turns it into
`None`, and gold scores an omission on every "return within 30 days" rule. That is part of the 149
above. "No number given" should be unscored (or a separate "unspecified" value), never "the NDA
has no return clause".

### 3. Planted clauses break unanchored pack rules without telling gold *(test)*

`Planter._clause_hits` only knows anchored forbid rules, the law topics and field rules. The shipped
packs have unanchored forbid rules that the library clauses break:

| Planted clause | Pack rule it also breaks, not recorded |
|---|---|
| penalty (`penalty_fixed`) | hospital P-25, manufacturer P-18 (no penalties, always apply) |
| non-compete (`noncompete_24m`) | saas P-24, hospital P-26 (no non-compete under California law) |
| residuals (the loophole clause) | saas P-09 (no residuals clause, always applies) |
| no-reporting (`no_reporting`) | also a Speak Out Act risk for employee deals (LAW-SPEAK-OUT) |

Gold keeps the natural "absent" term label, so a system that correctly flags the planted clause is
charged a false alarm. Distractors are worst: the penalty clause is planted as a distractor when
LAW-PENALTY doesn't apply (non-US law), yet the pack's own no-penalty rule always applies. So the
"distractor" is a real violation.

Checked: after planting a penalty clause in a hospital NDA, gold lists LAW-PENALTY but scores P-25
as compliant.

**Fix:** give unanchored forbid rules a library topic (the way `LAW_TOPICS` does for law
provisions) so `_safe` and the gold mapping see them. Or let `gold_for` mark every unanchored rule
unscored when an inserted clause matches its topic.

### 4. Counterparty type is invented, then law rules are scored on it

`generate_deals` assigns company and counterparty type round-robin, ignoring what the NDA is.
A quarter of NDAs become "employee" deals, so every DTSA rule (LAW-DTSA-1833B, saas P-28,
manufacturer P-30) expects a whistleblower notice. Gold then marks a statutory risk on an ordinary
company-to-company NDA that the DTSA notice rule doesn't apply to. The same goes for the vendor-only
CCPA rule, and for the hospital pack being applied to a manufacturing NDA.

**Fix:** have the labellers record the counterparty kind (company vs individual) and only draw
types that fit: employee only for NDAs with an individual. Or drop the employee type from the draw
and test the DTSA rules on planted employee NDAs.

## Moderate: these make comparisons unreliable

### 5. A deal depends on which other NDAs are in the run *(test)*

The company and counterparty come from the NDA's position in the sorted id list, and the random
draws follow the same order. Running a different subset gives the same NDA a different deal.
Checked: NDA 10 is company B in a run of [5, 10, 15] but company A in a run of [10, 15].

Prefix runs (`--limit 20` on the same split) happen to be stable. Any other subset, a different
pack order on the command line, or a planted filter isn't. That breaks paired comparisons between
runs. **Fix:** seed each NDA's draw from `(seed, doc_id)` and pick company and type from a hash of
the id.

### 6. "3 deal draws per NDA" (proposal §7) barely draws anything *(test)*

Across seeds, company and counterparty type never change. Personal data comes from the label
whenever it's known, which is 152 of 184 NDAs. So a new seed only changes country, value band and
personal data for 32 NDAs. The draws add almost no variance. **Fix:** draw company and type from
the seed too (point 5's fix does this).

### 7. The company is never on the receiving side *(test)*

`company_side` is only ever "mutual" or "disclosing". Hospital P-13 and P-27
(`company_side == 'receiving'`) can never apply, and manufacturer P-23 (`== 'disclosing'`) never
applies to mutual NDAs.

### 8. Hidden and visible facts score different rule sets

For the 32 NDAs where personal data is unknown, the form gets a random value (50/50). Without
`--hide-facts`, rules that depend on personal data are scored on that coin flip. With
`--hide-facts`, gold sees the fact as unknown and leaves those rules unscored. The planter always
uses the form, so personal-data defects planted on these NDAs silently vanish from gold in
hide-facts runs.

Hide-facts is the headline H1 setting, so the denominators differ between the runs being compared.
**Fix:** don't draw a value. Leave personal data unknown on the form for these NDAs in both modes,
or exclude them.

## Pack content: gold is only as good as the rules it scores

### 9. Some anchored "require" rules point the wrong way for a disclosing company

These rules require the NDA to give the receiving side something:

- **saas:** P-17 (may share with third parties, nda-7), P-27 (may acquire similar information,
  nda-13), P-29 (may make copies, nda-17)
- **hospital:** P-28 (may independently develop, nda-12)
- **manufacturer:** P-16 (nda-7), P-17 (nda-13), P-22 (nda-17)

With these, a strict NDA that doesn't permit copies or third-party sharing is scored as an
*omission*, and the repair loop would be rewarded for adding receiving-party freedoms. Each anchor
needs a person to confirm it means what the company wants. That is the REVIEW.md anchor section,
still unticked.

### 10. Rules that duplicate the law pack, or each other, double-count

- The DTSA notice is checked three times for employee deals in saas and manufacturer: LAW-DTSA-1833B
  plus saas P-28 or manufacturer P-30.
- Non-competes under California law are checked twice: LAW-CA-BPC-16600 plus saas P-24 or
  hospital P-26.
- Penalties are checked twice: LAW-PENALTY plus hospital P-25 or manufacturer P-18.
- Hospital P-06 and P-11 are both anchored to nda-16, so every missing return clause is two
  omissions on personal-data deals.

One real defect becomes two or three gold defects. **Fix:** drop the duplicated pack rules, or
score duplicates as one.

### 11. The California switch adds unrecorded extra defects

Thirty NDAs are switched to California law. In saas and manufacturer, that switch is also a
governing-law deviation (P-22, P-21). Gold does score these, through `field_overrides`, so they are
not lost. But they are outside the planter's 2–4 count and break the "a planted edit may not break
any other rule" claim.

## Minor

- Field violations, natural term-label defects and omissions all carry no gold evidence, so the
  strict "both citations correct" score only checks clause citations for anchored defects. Report
  `n_gold_with_evidence` next to every strict score.
- `gold_deal` keeps an NDA with no governing law as unknown (None), while the reviewer writes
  "unknown". The two agree in effect, but the asymmetry is easy to break.

## Suggested order of fixes

1. Field-rule semantics for missing and unreadable values (points 1 and 2), in both gold and the
   reviewer.
2. Planter tracking of unanchored pack rules (point 3).
3. Deals keyed by doc id, with real draws and a sensible counterparty kind (points 4–8).
4. A person reviews the anchors and the duplicates in the packs (points 9 and 10).

After fixes 1–3, the pilot numbers should be re-run.
