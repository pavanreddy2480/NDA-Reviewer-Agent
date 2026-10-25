"""NDA labels and deal contexts (proposal §6): field rules and other rules are labelled
independently by two models; a person settles every disagreement and checks a 20% sample of
agreements; label accuracy is reported; unclear labels are left unscored. Deals spread over the
three companies and four counterparty types, with 3 deal draws per NDA (§7)."""

import pytest
import yaml

from conftest import make_doc, make_law_pack, make_pack
from counselcopilot.benchmark.autolabel import (autolabel, autolabel_from_answers, label_accuracy, merge,
                                                normalise_answer, rule_terms, term_key, write_autolabels)
from counselcopilot.benchmark.deals import generate_deals, load_deals, save_deals
from counselcopilot.benchmark.gold import DISPUTED, NO_LAW
from counselcopilot.benchmark.labels import load_labels, prefill, usable, write_prefilled
from counselcopilot.llm import FakeClient
from counselcopilot.policy.schema import CounterpartyType


def raw(**kw):
    base = {"is_template": False, "mutual": True, "parties": ["A", "B"], "disclosing_party": "A",
            "governing_law": "State of Delaware", "personal_data": False, "confidentiality_term_months": "3 years",
            "survival_months": None, "return_deadline_days": "30 days", "non_solicit_months": None,
            "dispute_forum": "Delaware", "non_compete": False}
    return {**base, **kw}


# ------------------------------------------------------------------ one labeller's answer

def test_answers_are_normalised_like_the_reviewer():
    lab = normalise_answer(raw())
    assert lab["governing_law"] == "delaware"
    assert lab["fields"]["confidentiality_term_months"] == 36.0
    assert lab["fields"]["return_deadline_days"] == 30.0
    assert lab["fields"]["survival_months"] is None


def test_no_governing_law_means_none_not_unknown():
    assert normalise_answer(raw(governing_law=None))["governing_law"] == NO_LAW


def test_template_blanks_stay_blank():
    assert normalise_answer(raw(confidentiality_term_months="blank"))["fields"]["confidentiality_term_months"] == "blank"


def test_personal_data_cannot_tell_stays_unknown():
    assert normalise_answer(raw(personal_data="maybe"))["personal_data"] is None


def test_unreadable_duration_is_not_recorded_as_absent():
    lab = normalise_answer(raw(confidentiality_term_months="until the deal closes"))
    assert lab["fields"]["confidentiality_term_months"] is not None


# ------------------------------------------------------------------ two labellers

def test_agreement_is_accepted_and_disagreement_is_disputed():
    a = normalise_answer(raw())
    b = normalise_answer(raw(governing_law="New York", confidentiality_term_months="36 months"))
    e = merge(a, b, ("m1", "m2"))
    assert e["fields"]["confidentiality_term_months"] == 36.0  # 3 years == 36 months
    assert e["governing_law"] == DISPUTED and "governing_law" in e["auto"]["disagree"]
    assert e["verified"] is False and e["company_party"] == "A"
    assert e["auto"]["answers"]["m1"]["governing_law"] == "delaware"


def test_term_labels_must_both_be_booleans_to_agree():
    t = {"LAW-DTSA-1833B": "notice", "X:P-01": "term"}
    a = normalise_answer({**raw(), "terms": {"LAW-DTSA-1833B": True, "X:P-01": True}}, t)
    b = normalise_answer({**raw(), "terms": {"LAW-DTSA-1833B": True, "X:P-01": "yes"}}, t)
    e = merge(a, b, ("m1", "m2"))
    assert e["terms"] == {"LAW-DTSA-1833B": True, "X:P-01": DISPUTED}


def test_a_fifth_of_agreed_entries_go_to_a_person():
    docs = [make_doc(doc_id=i) for i in range(1, 21)]
    same = {d.id: raw() for d in docs}
    out = autolabel_from_answers(docs, same, same, ("m1", "m2"), sample_share=0.2)
    audited = [i for i, e in out.items() if e["auto"].get("audit")]
    assert len(audited) == 4 and all(out[i]["auto"]["needs_person"] for i in audited)
    assert sum(e["auto"]["needs_person"] for e in out.values()) == 4


def test_every_disagreement_goes_to_a_person():
    docs = [make_doc(doc_id=1), make_doc(doc_id=2)]
    out = autolabel_from_answers(docs, {1: raw(), 2: raw()}, {1: raw(mutual=False), 2: raw()}, ("a", "b"),
                                 sample_share=0.0)
    assert out[1]["auto"]["needs_person"] and not out[2]["auto"]["needs_person"]


def test_doc_missing_an_answer_is_skipped():
    docs = [make_doc(doc_id=1), make_doc(doc_id=2)]
    assert set(autolabel_from_answers(docs, {1: raw(), 2: raw()}, {1: raw()}, ("a", "b"))) == {1}


def test_autolabel_calls_both_models():
    import json

    a, b = FakeClient(lambda r: json.dumps(raw())), FakeClient(lambda r: json.dumps(raw(mutual=False)))
    out = autolabel([make_doc()], a, b, ("a", "b"), workers=1)
    assert out[1]["mutual"] == DISPUTED and a.requests and b.requests


def test_verified_labels_are_never_overwritten(tmp_path):
    path = tmp_path / "labels.yaml"
    path.write_text(yaml.safe_dump({1: {"verified": True, "governing_law": "ohio"}, 3: {"verified": False}}))
    stats = write_autolabels({1: {"verified": False, "governing_law": "texas", "auto": {}},
                              2: {"verified": False, "auto": {"disagree": ["mutual"], "needs_person": True}}}, path)
    saved = yaml.safe_load(path.read_text())
    assert saved[1]["governing_law"] == "ohio" and 3 in saved and stats["need_person"] == 1


def test_label_accuracy_on_audited_entries():
    labels = {1: {"verified": True, "terms": {}, "auto": {"audit": True, "corrected": ["governing_law"]}},
              2: {"verified": True, "terms": {}, "auto": {"audit": True}},
              3: {"verified": False, "auto": {"audit": True}}}  # not yet checked
    acc = label_accuracy(labels)
    assert acc["audited_entries"] == 2 and acc["entries_fully_correct"] == 1
    assert acc["key_accuracy"] == pytest.approx(1 - 1 / acc["keys_checked"])


def test_term_keys_and_which_rules_need_presence_labels():
    assert term_key("Co", "P-01") == "Co:P-01" and term_key("Co", "LAW-PENALTY") == "LAW-PENALTY"
    terms = rule_terms(list(make_pack().rules) + make_law_pack().as_rules(), "TestCo")
    assert set(terms) == {"LAW-CA-BPC-16600", "LAW-DTSA-1833B", "LAW-PENALTY"}  # anchored and field rules excluded


# ------------------------------------------------------------------ hand labels

def test_prefill_reads_template_mutual_and_governing_law():
    doc = make_doc(["MUTUAL NDA between ____ and ____.",
                    "This Agreement shall be governed by the laws of the State of New York."])
    p = prefill(doc)
    assert p["is_template"] and p["mutual"] and p["governing_law"] == "new york" and not p["verified"]


def test_prefill_never_invents_a_jurisdiction():
    doc = make_doc(["This Agreement is governed by the laws of Whatever Place Incorporated."])
    assert prefill(doc)["governing_law"] == "unknown"


def test_only_verified_or_auto_entries_are_used(tmp_path):
    path = tmp_path / "l.yaml"
    path.write_text(yaml.safe_dump({1: {"verified": True}, 2: {"verified": False}, 3: {"verified": False, "auto": {"by": []}}}))
    assert set(load_labels(path)) == {1}
    assert set(load_labels(path, allow_auto=True)) == {1, 3}
    assert set(load_labels(path, allow_unverified=True)) == {1, 2, 3}
    assert load_labels(tmp_path / "missing.yaml") == {} and load_labels(None) == {}
    assert usable({"verified": True}) and not usable({"auto": {"by": []}})


def test_write_prefilled_keeps_human_work(tmp_path):
    path = tmp_path / "l.yaml"
    path.write_text(yaml.safe_dump({1: {"verified": True, "governing_law": "ohio"}}))
    write_prefilled([make_doc(doc_id=1), make_doc(doc_id=2)], path)
    saved = yaml.safe_load(path.read_text())
    assert saved[1]["governing_law"] == "ohio" and saved[2]["verified"] is False


# ------------------------------------------------------------------ deal contexts

def test_deals_spread_over_companies_and_counterparty_types():
    deals = generate_deals(list(range(1, 25)), ["A", "B", "C"])
    assert {d.company for d in deals.values()} == {"A", "B", "C"}
    assert {d.counterparty_type for d in deals.values()} == set(CounterpartyType)
    assert all(d.governing_law is None for d in deals.values())  # never on the form


def test_deals_are_deterministic_and_differ_by_seed():
    a, b = generate_deals([1, 2, 3, 4], ["A"], seed=0), generate_deals([4, 3, 2, 1], ["A"], seed=0)
    assert a == b
    draws = [generate_deals(list(range(30)), ["A"], seed=s) for s in range(3)]  # 3 deal draws per NDA
    assert draws[0] != draws[1] != draws[2]


def test_deal_form_agrees_with_the_nda_labels():
    deals = generate_deals([1, 2], ["A"], labels={1: {"personal_data": True, "mutual": True},
                                                  2: {"personal_data": False}})
    assert deals[1].personal_data is True and deals[1].company_side == "mutual"
    assert deals[2].personal_data is False and deals[2].company_side == "disclosing"


def test_deals_round_trip(tmp_path):
    deals = generate_deals([1, 2, 3], ["A", "B"])
    save_deals(deals, tmp_path / "d" / "deals.json")
    assert load_deals(tmp_path / "d" / "deals.json") == deals


# ------------------------------------------------------------------ logic audit, 25 Oct (docs/reviews/gold-deals-audit.md)

def test_an_ndas_deal_does_not_depend_on_which_other_ndas_are_in_the_run():
    a = generate_deals([5, 10, 15], ["A", "B", "C"])
    b = generate_deals([10, 15], ["A", "B", "C"])
    assert (a[10].company, a[10].counterparty_type) == (b[10].company, b[10].counterparty_type)


def test_deal_draws_vary_company_or_counterparty():
    draws = [generate_deals(list(range(30)), ["A", "B", "C"], seed=s) for s in range(3)]
    assert any((draws[0][i].company, draws[0][i].counterparty_type) != (d[i].company, d[i].counterparty_type)
               for d in draws[1:] for i in range(30))


@pytest.mark.xfail(strict=True, reason="GAP: the company is never on the receiving side, so rules conditioned on "
                                        "company_side == 'receiving' (hospital P-13, P-27) can never apply")
def test_deals_include_the_receiving_side():
    deals = generate_deals(list(range(200)), ["A"], labels={i: {"mutual": False} for i in range(200)})
    assert "receiving" in {d.company_side for d in deals.values()}


# ------------------------------------------------------------------ counterparty facts read from the NDA (25 Oct)

from counselcopilot.benchmark.autolabel import add_counterparty_labels, normalise_counterparty  # noqa: E402
from counselcopilot.benchmark.deals import deal_for, deal_sources  # noqa: E402


def test_counterparty_role_and_country_come_from_the_label():
    d = deal_for(7, ["A", "B", "C"], {"counterparty_role": "customer", "counterparty_kind": "company",
                                      "counterparty_country": "germany"})
    assert d.counterparty_type == "customer" and d.counterparty_country == "germany" and d.variables()["foreign"]
    assert deal_sources({"counterparty_role": "customer", "counterparty_country": "germany"})[
        "counterparty_type"] == "label"


def test_an_individual_counterparty_is_an_employee_type_deal():
    assert deal_for(7, ["A"], {"counterparty_kind": "individual", "counterparty_role": "unknown"}
                    ).counterparty_type == "employee"


def test_a_company_with_unknown_role_is_never_an_employee():
    types = {deal_for(i, ["A"], {"counterparty_kind": "company", "counterparty_role": "unknown"}).counterparty_type
             for i in range(200)}
    assert types == {"vendor", "customer", "partner"}


def test_no_invented_foreign_counterparties():
    """We are a US benchmark: a country the NDA doesn't state is the US, never a random foreign one."""
    deals = generate_deals(list(range(200)), ["A"], labels={i: {"counterparty_country": None} for i in range(200)})
    assert {d.counterparty_country for d in deals.values()} == {"US"}
    us = deal_for(1, ["A"], {"counterparty_country": "united states"})
    assert us.counterparty_country == "US" and not us.variables()["foreign"]


def test_unknown_personal_data_is_left_blank_not_drawn():
    assert deal_for(1, ["A"], {"personal_data": None}).personal_data is None
    assert deal_for(1, ["A"], {"personal_data": "disputed"}).personal_data is None


def test_assigned_facts_are_marked():
    src = deal_sources({})
    assert src["counterparty_type"] == "assigned" and src["counterparty_country"] == "assigned"
    assert src["personal_data"] == "unknown"


def test_counterparty_answers_are_normalised():
    out = normalise_counterparty({"counterparty_kind": "Company", "counterparty_role": "supplier",
                                  "counterparty_country": "a Delaware corporation"})
    assert out == {"counterparty_kind": "unknown", "counterparty_role": "unknown",
                   "counterparty_country": "united states"}


def test_counterparty_labels_merge_into_existing_entries():
    labels = {1: {"verified": False, "governing_law": "ohio", "auto": {"disagree": ["mutual"]}},
              2: {"verified": False, "auto": {"disagree": []}},
              3: {"verified": True, "counterparty_role": "vendor", "auto": {}}}
    a = {1: {"counterparty_kind": "company", "counterparty_role": "vendor", "counterparty_country": "Texas"},
         2: {"counterparty_kind": "company", "counterparty_role": "customer", "counterparty_country": None},
         3: {"counterparty_kind": "company", "counterparty_role": "partner", "counterparty_country": None}}
    b = {1: {"counterparty_kind": "company", "counterparty_role": "vendor", "counterparty_country": "USA"},
         2: {"counterparty_kind": "company", "counterparty_role": "partner", "counterparty_country": None},
         3: {"counterparty_kind": "company", "counterparty_role": "partner", "counterparty_country": None}}
    stats = add_counterparty_labels(labels, a, b, ("sonnet", "haiku"))
    assert labels[1]["counterparty_role"] == "vendor" and labels[1]["counterparty_country"] == "united states"
    assert labels[1]["governing_law"] == "ohio" and labels[1]["auto"]["disagree"] == ["mutual"]
    assert labels[2]["counterparty_role"] == DISPUTED and labels[2]["auto"]["needs_person"]
    assert labels[3]["counterparty_role"] == "vendor"  # a person's verified value is kept
    assert stats["disputed_keys"] == 1


def test_disputed_role_is_assigned_not_read():
    assert deal_sources({"counterparty_role": DISPUTED})["counterparty_type"] == "assigned"
