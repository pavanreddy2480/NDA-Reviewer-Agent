"""RQ1: applicability-aware two-way retrieval (proposal §3, §4 Figure 2, §7 baselines and ablations).

- the reverse path (applicable rule -> NDA segments) is the only way to find a missing clause;
- the forward path (NDA segment -> rules) finds violations only;
- the deal filter stops rules that don't apply to this deal from firing;
- B4 checks every rule against the whole NDA, with and without the deal filter;
- every system in a comparison sends its checks to the same checker model.
"""

import pytest

from conftest import COMPLIANT_SEGMENTS, KeywordLLM, make_law_pack, make_pack
from counselcopilot.data.draft import Draft
from counselcopilot.policy.schema import DealContext
from counselcopilot.review.findings import FindingType
from counselcopilot.review.policy_reviewer import PolicyReviewer, ReviewConfig, rule_query

FIELDS = {"confidentiality_term_months": "four (4) years", "governing_law": "Delaware"}
HINTS = {"confidentiality_term_months": "years", "governing_law": "governed"}

# no return/destroy clause (P-01 omission), a non-solicit (P-03 violation for customers),
# a non-compete (§16600 risk under California law)
DEFECTIVE = Draft("bad", [
    "MUTUAL NON-DISCLOSURE AGREEMENT",
    "Confidential Information includes information disclosed orally or in writing.",
    "Neither party shall solicit or hire the other party's employees for twelve (12) months.",
    "The obligations of confidentiality last for four (4) years.",
    "For two years neither party shall compete with the other in any market.",
    "This Agreement is governed by the laws of the State of Delaware.",
])
CLEAN = Draft("clean", list(COMPLIANT_SEGMENTS))


def form(**kw) -> DealContext:
    return DealContext(**{"company": "TestCo", "counterparty_type": "vendor", "personal_data": False,
                          "governing_law": "delaware", **kw})


def review(draft=DEFECTIVE, d=None, preset="full", llm=None, law=False, **cfg):
    llm = llm or KeywordLLM(fields=FIELDS, field_hints=HINTS)
    c = ReviewConfig.preset(preset)
    c.max_workers = 1
    for k, v in cfg.items():
        setattr(c, k, v)
    rev = PolicyReviewer(llm, make_pack(), c, law_pack=make_law_pack() if law else None)
    return rev.review(draft, d or form()), llm


def found(result) -> set[tuple[str, str]]:
    return {(f.rule_id, f.type.value) for f in result.findings}


# ------------------------------------------------------------------ presets

def test_presets_match_the_proposal_systems():
    p = ReviewConfig.preset
    assert (p("full").reverse, p("full").forward, p("full").applicability_filter) == (True, True, True)
    assert not p("no_reverse").reverse and p("no_reverse").forward
    assert not p("no_filter").applicability_filter
    assert p("exhaustive").exhaustive and not p("exhaustive").applicability_filter
    assert p("exhaustive_filtered").exhaustive and p("exhaustive_filtered").applicability_filter
    with pytest.raises(KeyError):
        p("long_context")


# ------------------------------------------------------------------ the reverse path finds omissions

def test_full_system_finds_omission_and_violation():
    res, _ = review(d=form(counterparty_type="partner"))
    assert ("P-01", "omission") in found(res)  # no return/destroy clause
    assert ("P-03", "violation") not in found(res)  # partner deal: non-solicit rule does not apply


def test_clean_nda_has_no_findings():
    res, _ = review(CLEAN, form(personal_data=True))
    assert res.findings == []


def test_forward_only_cannot_report_omissions():
    """The clean RQ1 ablation: without the reverse path a missing clause is invisible."""
    res, _ = review(d=form(counterparty_type="customer"), preset="no_reverse")
    assert not any(f.type == FindingType.OMISSION for f in res.findings)
    assert ("P-03", "violation") in found(res)


def test_forward_only_drops_field_omissions_too():
    llm = KeywordLLM(fields={"governing_law": None, "confidentiality_term_months": None}, field_hints=HINTS)
    full, _ = review(d=form(), llm=llm)
    fwd, _ = review(d=form(), llm=KeywordLLM(fields={"governing_law": None, "confidentiality_term_months": None}),
                    preset="no_reverse")
    assert ("P-05", "omission") in found(full)
    assert not any(f.type == FindingType.OMISSION for f in fwd.findings)


def test_forward_only_keeps_field_violations():
    llm = KeywordLLM(fields={**FIELDS, "confidentiality_term_months": "perpetual"}, field_hints=HINTS)
    res, _ = review(d=form(), preset="no_reverse", llm=llm)
    assert ("P-06", "violation") in found(res)


def test_forward_hits_are_merged_into_one_two_way_check_per_rule():
    res, llm = review(d=form(counterparty_type="customer"))
    p03 = [c for c in res.checks if c.rule_id == "P-03"]
    assert len(p03) == 1 and p03[0].direction in ("two_way", "reverse")
    assert len(llm.prompts_with("STATEMENT: A party shall not solicit")) == 1


# ------------------------------------------------------------------ the deal filter

def test_deal_filter_stops_non_applicable_rules_from_firing():
    vendor, _ = review(d=form(counterparty_type="vendor"))
    assert ("P-03", "violation") not in found(vendor)  # non-solicit is only forbidden for customers
    assert "P-03" not in vendor.rules_in_scope and "P-03" not in vendor.applicable_rules


def test_without_the_filter_the_distractor_fires():
    res, _ = review(d=form(counterparty_type="vendor"), preset="no_filter")
    assert ("P-03", "violation") in found(res)
    assert "P-03" in res.rules_in_scope and "P-03" not in res.applicable_rules


def test_applicable_rules_are_reported_the_same_for_every_preset():
    sets = {p: tuple(review(d=form(counterparty_type="customer"), preset=p)[0].applicable_rules)
            for p in ("full", "no_reverse", "no_filter", "exhaustive", "exhaustive_filtered")}
    assert len(set(sets.values())) == 1


def test_applicability_uses_facts_read_from_the_nda():
    """H1 with deal facts left off the form: the reviewer reads personal data from the NDA,
    which switches on the 36-month minimum (P-04)."""
    blank = form(personal_data=None, governing_law=None)
    pd_llm = KeywordLLM(fields=FIELDS, field_hints=HINTS, personal_data=True)
    no_pd_llm = KeywordLLM(fields=FIELDS, field_hints=HINTS, personal_data=False)
    with_pd, _ = review(d=blank, llm=pd_llm)
    without, _ = review(d=blank, llm=no_pd_llm)
    assert "P-04" in with_pd.applicable_rules and "P-04" not in without.applicable_rules
    assert with_pd.deal.personal_data is True and with_pd.deal.governing_law == "delaware"
    assert {f.name for f in with_pd.inferred_facts} == {"personal_data", "governing_law"}


def test_state_law_read_from_the_nda_switches_on_state_statutes():
    blank = form(governing_law=None)
    ca = KeywordLLM(fields={**FIELDS, "governing_law": "California"}, field_hints=HINTS)
    de = KeywordLLM(fields=FIELDS, field_hints=HINTS)
    under_ca, _ = review(d=blank, llm=ca, law=True)
    under_de, _ = review(d=blank, llm=de, law=True)
    assert ("LAW-CA-BPC-16600", "statutory_risk") in found(under_ca)
    assert ("P-05", "approval_needed") in found(under_ca)  # foreign-to-policy law needs the General Counsel
    assert "LAW-CA-BPC-16600" not in under_de.applicable_rules
    assert not any(f.rule_id.startswith("LAW-CA") for f in under_de.findings)


def test_dtsa_notice_missing_from_employee_nda_is_a_statutory_risk():
    res, _ = review(d=form(counterparty_type="employee"), law=True)
    assert ("LAW-DTSA-1833B", "statutory_risk") in found(res)


# ------------------------------------------------------------------ B4 exhaustive checking

def test_exhaustive_shows_the_whole_nda_to_every_check():
    res, _ = review(d=form(counterparty_type="customer"), preset="exhaustive")
    n = len(DEFECTIVE.segments)
    term_checks = [c for c in res.checks if c.direction == "exhaustive"]
    assert term_checks and all(c.result.shown == list(range(n)) for c in term_checks)


def test_exhaustive_without_filter_checks_every_rule():
    res, _ = review(d=form(counterparty_type="vendor"), preset="exhaustive", law=True)
    every = {r.id for r in make_pack().rules} | {r.id for r in make_law_pack().as_rules()}
    assert {c.rule_id for c in res.checks} == every


def test_exhaustive_filtered_checks_only_applicable_rules():
    res, _ = review(d=form(counterparty_type="vendor"), preset="exhaustive_filtered", law=True)
    assert {c.rule_id for c in res.checks} == set(res.applicable_rules)


def test_full_and_exhaustive_filtered_agree_on_a_small_nda():
    """Same applicability and same checker; when retrieval returns every segment, the two
    systems must report the same findings (any RQ1 gap then comes from retrieval)."""
    full, _ = review(d=form(counterparty_type="customer"))
    exh, _ = review(d=form(counterparty_type="customer"), preset="exhaustive_filtered")
    assert found(full) == found(exh)


def test_retrieval_shows_fewer_segments_than_exhaustive():
    long = Draft("long", DEFECTIVE.segments + [f"Boilerplate clause number {i} about notices." for i in range(40)])
    full, _ = review(long, form(counterparty_type="customer"), k_segments=3, neighbours=0)
    exh, _ = review(long, form(counterparty_type="customer"), preset="exhaustive_filtered")
    shown = lambda r: sum(len(c.result.shown) for c in r.checks if c.direction != "field")
    assert shown(full) < shown(exh)


@pytest.mark.xfail(strict=True, reason="PROPOSAL MISMATCH: H1 says the full system matches B4+filter 'while making "
                                        "fewer checks', but both make exactly one check per applicable rule by "
                                        "construction; the saving can only be in tokens per check")
def test_full_system_makes_fewer_checks_than_exhaustive_filtered():
    full, _ = review(d=form(counterparty_type="customer"), law=True)
    exh, _ = review(d=form(counterparty_type="customer"), preset="exhaustive_filtered", law=True)
    assert full.n_checks < exh.n_checks


# ------------------------------------------------------------------ fairness and robustness

def test_every_check_goes_to_the_checker_model():
    main = KeywordLLM(fields=FIELDS, field_hints=HINTS, personal_data=True, name="backbone")
    checker = KeywordLLM(fields=FIELDS, field_hints=HINTS, name="checker")
    cfg = ReviewConfig.preset("full")
    cfg.max_workers = 1
    PolicyReviewer(main, make_pack(), cfg, checker_llm=checker).review(DEFECTIVE, form(personal_data=None))
    assert main.check_requests() == [] and checker.check_requests()
    # the backbone only reads deal facts; field rules are answered by the checker as well
    assert len(main.requests) == 1 and "personal data" in main.requests[0].messages[0].content
    assert checker.prompts_with("How long do the confidentiality obligations last")


def test_failed_checks_are_counted_not_reported():
    res, _ = review(d=form(), llm=KeywordLLM(broken=True))
    assert res.findings == [] and res.n_errors == res.n_checks > 0


def test_neighbours_keep_an_exception_next_to_its_clause():
    rev = PolicyReviewer(KeywordLLM(), make_pack(), ReviewConfig(neighbours=1))
    assert rev._expand([0, 5], 6) == [0, 1, 4, 5]
    assert PolicyReviewer(KeywordLLM(), make_pack(), ReviewConfig(neighbours=0))._expand([3], 6) == [3]


def test_rule_query_uses_title_term_and_keywords():
    q = rule_query(make_pack().rule("P-01"))
    assert "Return or destruction" in q and "destroy" in q and "return" in q


def test_forward_index_is_chunked_by_rule():
    """Proposal §4: policies are chunked by rule, so a rule's exception stays with it."""
    rev = PolicyReviewer(KeywordLLM(), make_pack(), ReviewConfig(forward_min_score=0.0))
    term_rules = [r for r in make_pack().rules if r.kind != "field"]
    cands = rev._forward_candidates(DEFECTIVE, term_rules)
    assert set(cands) <= {r.id for r in term_rules}
    assert 2 in cands["P-03"]  # the non-solicit segment points at the non-solicit rule


def test_seeded_runs_pass_temperature_and_seed_to_the_checker():
    res, llm = review(d=form(), temperature=0.7, seed=3)
    checks = llm.check_requests()
    assert checks and all(r.temperature == 0.7 and r.seed == 3 for r in checks)
