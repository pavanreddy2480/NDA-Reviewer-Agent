"""Field rules (proposal §4: numbers and conditions are compared exactly, not by text
similarity) and deal facts read from the NDA (proposal H1: deal facts left off the form, so
applicability must be inferred from the NDA)."""

import json

import pytest

from conftest import KeywordLLM, make_pack
from counselcopilot.data.draft import Draft
from counselcopilot.llm import FakeClient, PendingBatch
from counselcopilot.policy.schema import DealContext
from counselcopilot.retrieval.index import HybridIndex, Passage
from counselcopilot.review.deal_facts import resolve_deal
from counselcopilot.review.fields import BLANK, UNSPECIFIED, _duration, _normalise, check_field_rule, extract_field
from counselcopilot.review.findings import FindingType

DRAFT = Draft("d1", [
    "Confidential Information includes information disclosed orally.",
    "The obligations of confidentiality last for four (4) years from the date of disclosure.",
    "This Agreement is governed by and construed under the laws of the State of Delaware.",
    "The parties may share employee records and customer personal data for the Purpose.",
])


def idx(d: Draft = DRAFT) -> HybridIndex:
    return HybridIndex([Passage(str(i), s) for i, s in enumerate(d.segments)])


PACK = make_pack()


# ------------------------------------------------------------------ normalising values

@pytest.mark.parametrize("text, unit, value", [
    ("2 years", "months", 24.0), ("two (2) years", "months", 24.0), ("36", "months", 36.0),
    ("eighteen months", "months", 18.0), ("perpetual", "months", 9999.0), ("indefinitely", "months", 9999.0),
    ("thirty (30) days", "days", 30.0), ("2 weeks", "days", 14.0), ("1 year", "days", 365.0),
    ("no number here", "months", None),
])
def test_duration_parsing(text, unit, value):
    assert _duration(text, unit) == value


@pytest.mark.parametrize("field, raw, value", [
    ("confidentiality_term_months", 48, 48.0),
    ("confidentiality_term_months", "five (5) years", 60.0),
    ("return_deadline_days", "30", 30.0),
    ("governing_law", "the State of New York", "new york"),
    ("governing_law", "England", "united kingdom"),
    ("non_compete", "yes", True), ("non_compete", False, False),
    ("survival_months", None, None), ("survival_months", "", None), ("survival_months", "null", None),
    ("confidentiality_term_months", "Blank", BLANK),
    ("return_deadline_days", "promptly", UNSPECIFIED), ("return_deadline_days", "Unspecified", UNSPECIFIED),
])
def test_normalise_field_values(field, raw, value):
    assert _normalise(field, raw) == value


def test_extract_field_cites_only_retrieved_segments():
    llm = KeywordLLM(fields={"governing_law": "Delaware"}, field_hints={"governing_law": "governed"})
    value, ev = extract_field(llm, "governing_law", DRAFT, idx())
    assert value == "delaware" and ev == [2]


# ------------------------------------------------------------------ checking field rules

def check(rule_id: str, fields: dict, d: Draft = DRAFT):
    llm = KeywordLLM(fields=fields, field_hints={"confidentiality_term_months": "years",
                                                 "governing_law": "governed"})
    return check_field_rule(llm, PACK.rule(rule_id), d, idx(d))


def test_compliant_field_is_no_finding():
    f, r = check("P-04", {"confidentiality_term_months": "four (4) years"})
    assert f is None and r.label == "Entailment"


def test_short_term_is_a_violation_citing_the_clause():
    f, r = check("P-04", {"confidentiality_term_months": "one (1) year"})
    assert f.type == FindingType.VIOLATION and f.evidence == [1] and f.direction == "field"


def test_missing_value_is_an_omission():
    f, _ = check("P-04", {"confidentiality_term_months": None})
    assert f.type == FindingType.OMISSION and f.evidence == []


def test_field_rule_with_approval_route_is_approval_needed():
    f, _ = check("P-05", {"governing_law": "California"})
    assert f.type == FindingType.APPROVAL_NEEDED


def test_min_and_max_rules_interact():
    """Proposal §4: lengthening a term for one rule can break another rule's maximum."""
    assert check("P-04", {"confidentiality_term_months": "perpetual"})[0] is None
    assert check("P-06", {"confidentiality_term_months": "perpetual"})[0].type == FindingType.VIOLATION
    assert check("P-04", {"confidentiality_term_months": "two (2) years"})[0] is not None
    assert check("P-06", {"confidentiality_term_months": "two (2) years"})[0] is None


def test_template_blank_is_neither_compliant_nor_an_omission():
    f, r = check("P-04", {"confidentiality_term_months": "blank"})
    assert f is None and "blank" in r.rationale


def test_no_clause_meets_a_maximum_only_rule():
    """Gold-deals audit, point 1: no confidentiality term at all doesn't break 'at most 60 months'."""
    f, r = check("P-06", {"confidentiality_term_months": None})
    assert f is None and "allows" in r.rationale


@pytest.mark.parametrize("field, op, value, ok", [
    ("non_solicit_months", "<=", 12, True), ("survival_months", ">=", 24, False),
    ("return_deadline_days", "<=", 30, False), ("return_deadline_days", ">=", 10, True),
    ("non_compete", "==", False, True), ("governing_law", "in", ["delaware"], False),
    ("governing_law", "not in", ["california"], True),
])
def test_what_an_absent_clause_meets(field, op, value, ok):
    from counselcopilot.policy.schema import FieldConstraint

    assert FieldConstraint(field=field, op=op, value=value).check_absent() is ok


def test_value_stated_without_a_number_is_no_finding():
    f, r = check("P-04", {"confidentiality_term_months": "until the transaction closes"})
    assert f is None and "without a number" in r.rationale


def test_extractor_is_told_about_unspecified_values():
    llm = KeywordLLM(fields={"confidentiality_term_months": 48})
    extract_field(llm, "confidentiality_term_months", DRAFT, idx())
    extract_field(llm, "governing_law", DRAFT, idx())
    assert ['"unspecified"' in r.messages[-1].content for r in llm.requests] == [True, False]


def test_malformed_field_reply_is_a_check_error():
    f, r = check_field_rule(KeywordLLM(broken=True), PACK.rule("P-04"), DRAFT, idx())
    assert f is None and r.error


def test_field_extraction_propagates_pending_batch():
    class Queued(FakeClient):
        def complete(self, *a, **k):
            raise PendingBatch("queued")

    with pytest.raises(PendingBatch):
        check_field_rule(Queued(), PACK.rule("P-04"), DRAFT, idx())


# ------------------------------------------------------------------ deal facts read from the NDA

BLANK_FORM = DealContext(company="TestCo", counterparty_type="vendor", personal_data=None, governing_law=None)


def test_blank_facts_are_read_from_the_nda():
    llm = KeywordLLM(personal_data=True, fields={"governing_law": "Delaware"})
    full, facts = resolve_deal(llm, BLANK_FORM, DRAFT, idx())
    assert full.personal_data is True and full.governing_law == "delaware"
    assert {f.name: f.value for f in facts} == {"personal_data": True, "governing_law": "delaware"}


def test_facts_on_the_form_are_not_re_inferred():
    llm = KeywordLLM(personal_data=True)
    form = DealContext(company="TestCo", counterparty_type="vendor", personal_data=False, governing_law="ohio")
    full, facts = resolve_deal(llm, form, DRAFT, idx())
    assert full == form and facts == [] and llm.requests == []


def test_nda_without_governing_law_gives_unknown_law():
    full, _ = resolve_deal(KeywordLLM(fields={"governing_law": None}), BLANK_FORM, DRAFT, idx())
    assert full.governing_law == "unknown" and not full.variables()["us_law"]


def test_malformed_fact_reply_leaves_the_fact_unknown():
    full, facts = resolve_deal(KeywordLLM(broken=True), BLANK_FORM, DRAFT, idx())
    assert full.personal_data is None and full.governing_law == "unknown"
    assert [f.value for f in facts] == [None, None]


def test_inferred_personal_data_evidence_must_be_shown():
    llm = FakeClient(lambda req: json.dumps({"rationale": "", "personal_data": True, "evidence": [3, 99]}))
    form = BLANK_FORM.model_copy(update={"governing_law": "delaware"})
    _, facts = resolve_deal(llm, form, DRAFT, idx())
    assert facts[0].evidence == [3]
