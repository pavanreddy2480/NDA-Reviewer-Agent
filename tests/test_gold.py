"""PolicyNDA ground truth without circularity (proposal §6).

Rules anchored to ContractNLI checks get each real NDA's natural omissions and violations from
the expert labels; field rules and other rules use the two-model labels; unclear labels are left
unscored, never counted as omissions; planted defects go on top."""

import pytest

from conftest import deal, make_doc, make_law_pack, make_pack
from counselcopilot.benchmark.gold import (DISPUTED, applicability, field_value, gold_deal, gold_for, known)
from counselcopilot.policy.schema import DealContext
from counselcopilot.review.findings import FindingType

PACK = make_pack()
LAW = make_law_pack()


def keys(g) -> set[tuple[str, str]]:
    return {(d.rule_id, d.type.value) for d in g.defects}


def gold(labels=None, nli=None, d=None, planted=None, law=None):
    doc = make_doc(labels=nli or {})
    return gold_for(doc, d or deal(), PACK, labels or {}, law, planted)


# ------------------------------------------------------------------ anchored rules use the expert labels

def test_not_mentioned_anchored_require_rule_is_a_natural_omission():
    g = gold(nli={"nda-3": ("Entailment", (1,))})
    assert ("P-01", "omission") in keys(g)  # nda-16 NotMentioned for a vendor
    assert ("P-02", "omission") not in keys(g)
    assert next(d for d in g.defects if d.rule_id == "P-01").evidence == ()


def test_contradicted_anchored_require_rule_is_a_natural_violation_with_evidence():
    g = gold(nli={"nda-16": ("Contradiction", (4,)), "nda-3": ("Entailment", (1,))})
    d = next(d for d in g.defects if d.rule_id == "P-01")
    assert (d.type, d.evidence, d.origin) == (FindingType.VIOLATION, (4,), "natural")


def test_entailed_forbid_rule_is_a_violation_only_when_it_applies():
    nli = {"nda-18": ("Entailment", (5,)), "nda-3": ("Entailment", (1,))}
    assert ("P-03", "violation") in keys(gold(nli=nli, d=deal(counterparty_type="customer")))
    g = gold(nli=nli, d=deal(counterparty_type="vendor"))
    assert ("P-03", "violation") not in keys(g) and "P-03" in g.not_applicable


# ------------------------------------------------------------------ field rules use the labels

def test_field_rules_scored_from_labels():
    labels = {"governing_law": "california", "fields": {"confidentiality_term_months": 120}}
    g = gold(labels, d=deal(personal_data=True, governing_law=None))
    assert ("P-05", "approval_needed") in keys(g)  # California law needs the General Counsel
    assert ("P-06", "violation") in keys(g)  # 120 > 60 months
    assert "P-04" in g.scored_rules and ("P-04", "violation") not in keys(g)


def test_no_governing_law_is_an_omission_but_unknown_law_is_unscored():
    g = gold({"governing_law": "none"}, d=deal(governing_law=None))
    assert ("P-05", "omission") in keys(g)
    g = gold({"governing_law": "unknown"}, d=deal(governing_law=None))
    assert "P-05" in g.unscored_rules and "P-05" not in {d.rule_id for d in g.defects}


@pytest.mark.parametrize("value", ["blank", DISPUTED, "unknown"])
def test_unclear_field_labels_are_unscored_never_omissions(value):
    g = gold({"fields": {"confidentiality_term_months": value}})
    assert "P-06" in g.unscored_rules
    assert all(d.rule_id != "P-06" for d in g.defects)


def test_field_absent_from_labels_is_unscored():
    assert "P-06" in gold({"fields": {}}).unscored_rules


def test_field_labelled_absent_is_an_omission():
    assert ("P-06", "omission") in keys(gold({"fields": {"confidentiality_term_months": None}}))


@pytest.mark.xfail(strict=True, reason="BUG: a labelled duration the parser can't read ('until the deal closes') "
                                        "normalises to None, and field_value then reports the term as absent, so "
                                        "gold counts an omission for a clause that is there")
def test_text_value_for_numeric_field_is_unscored():
    g = gold({"fields": {"confidentiality_term_months": "until the deal closes"}})
    assert "P-06" in g.unscored_rules
    assert ("P-06", "omission") not in keys(g)


# ------------------------------------------------------------------ unanchored rules use `terms` labels

def law_gold(terms, **kw):
    return gold({"terms": terms}, d=deal(counterparty_type="employee", governing_law="california"), law=LAW, **kw)


def test_unanchored_law_rules_use_presence_labels():
    g = law_gold({"LAW-DTSA-1833B": False, "LAW-CA-BPC-16600": True})
    assert ("LAW-DTSA-1833B", "statutory_risk") in keys(g)
    assert ("LAW-CA-BPC-16600", "statutory_risk") in keys(g)
    g = law_gold({"LAW-DTSA-1833B": True, "LAW-CA-BPC-16600": False})
    assert not any(d.rule_id.startswith("LAW-") for d in g.defects)


def test_disputed_or_missing_term_labels_are_unscored():
    g = law_gold({"LAW-DTSA-1833B": DISPUTED})
    assert {"LAW-DTSA-1833B", "LAW-CA-BPC-16600"} <= set(g.unscored_rules)


def test_pack_term_labels_are_keyed_by_company():
    pack = make_pack(rules=[{"id": "P-01", "title": "x", "requirement": "x", "kind": "require", "term": "X."}])
    doc = make_doc()
    assert gold_for(doc, deal(), pack, {"terms": {"P-01": False}}).unscored_rules == ["P-01"]
    g = gold_for(doc, deal(), pack, {"terms": {"TestCo:P-01": False}})
    assert {(d.rule_id, d.type.value) for d in g.defects} == {("P-01", "omission")}


def test_present_term_after_planter_edited_text_is_unscored():
    g = law_gold({"LAW-DTSA-1833B": True}, planted={"edited": True})
    assert "LAW-DTSA-1833B" in g.unscored_rules
    g = law_gold({"LAW-DTSA-1833B": False}, planted={"edited": True})  # absent stays absent
    assert ("LAW-DTSA-1833B", "statutory_risk") in keys(g)


# ------------------------------------------------------------------ applicability on the gold deal

def test_blank_facts_are_taken_from_labels():
    form = DealContext(company="TestCo", counterparty_type="vendor", personal_data=None, governing_law=None)
    g = gold_deal(form, {"personal_data": True, "governing_law": "State of New York"})
    assert g.personal_data is True and g.governing_law == "new york"


def test_facts_on_the_form_win_over_labels():
    g = gold_deal(deal(personal_data=False, governing_law="Delaware"), {"personal_data": True})
    assert g.personal_data is False and g.governing_law == "delaware"


def test_unknown_fact_that_decides_applicability_makes_the_rule_unscored():
    form = DealContext(company="TestCo", counterparty_type="vendor", personal_data=None)
    g = gold({"personal_data": None}, d=form)
    assert "P-04" in g.unscored_rules  # applies only with personal data
    assert "P-02" in g.scored_rules  # applies either way


def test_applicability_tries_every_value_the_condition_mentions():
    ca = next(r for r in LAW.as_rules() if r.id == "LAW-CA-BPC-16600")
    unknown_law = DealContext(company="X", counterparty_type="vendor", governing_law=None)
    assert applicability(ca, unknown_law) is None
    assert applicability(ca, unknown_law.model_copy(update={"governing_law": "california"})) is True
    assert applicability(PACK.rule("P-02"), unknown_law) is True


def test_known_placeholders():
    assert not any(known(v) for v in (None, "", "unknown", "blank", "disputed", "none", " Unknown "))
    assert known("delaware") and known(False) and known(0)


def test_field_value_after_planting():
    r = PACK.rule("P-06")
    assert field_value(r, {"fields": {"confidentiality_term_months": 24}}) == (True, 24.0)
    assert field_value(r, {}, {"field_overrides": {"confidentiality_term_months": 12.0}}) == (True, 12.0)
    assert field_value(r, {"fields": {"confidentiality_term_months": 24}},
                       {"touched_fields": ["confidentiality_term_months"]}) == (False, None)


# ------------------------------------------------------------------ planted defects

def test_planted_override_counts_as_planted():
    planted = {"overrides": {"nda-16": ("NotMentioned", [])}}
    g = gold(nli={"nda-16": ("Entailment", (2,))}, planted=planted)
    d = next(d for d in g.defects if d.rule_id == "P-01")
    assert d.origin == "planted" and d.type == FindingType.OMISSION


def test_touched_hypothesis_makes_its_rules_unscored():
    g = gold(nli={"nda-16": ("Entailment", (2,))}, planted={"touched_hypotheses": ["nda-16"]})
    assert "P-01" in g.unscored_rules


def test_evidence_is_remapped_to_the_planted_draft():
    g = gold(nli={"nda-16": ("Contradiction", (2, 3))}, planted={"index_map": {2: 5, 3: 6}})
    assert next(d for d in g.defects if d.rule_id == "P-01").evidence == (5, 6)


def test_planted_defect_on_non_applicable_rule_is_dropped():
    from counselcopilot.benchmark.gold import GoldDefect

    planted = {"defects": [GoldDefect("P-03", FindingType.VIOLATION, (7,), "planted")]}
    assert ("P-03", "violation") not in keys(gold(planted=planted, d=deal(counterparty_type="vendor")))
    g = gold(planted=planted, d=deal(counterparty_type="customer"))
    assert ("P-03", "violation") in keys(g) and "P-03" in g.scored_rules


def test_every_rule_is_scored_unscored_or_not_applicable_exactly_once():
    g = gold({"governing_law": "unknown", "terms": {"LAW-DTSA-1833B": False}}, law=LAW,
             d=deal(governing_law=None, counterparty_type="customer"))
    every = [r.id for r in PACK.rules] + [r.id for r in LAW.as_rules()]
    seen = g.scored_rules + g.unscored_rules + g.not_applicable
    assert sorted(seen) == sorted(every)
