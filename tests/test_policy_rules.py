"""Proposal §4: the compiled rule base. Every rule has an ID, an applicability condition
(e.g. vendor AND personal_data), a requirement and its source text; the US law pack is checked
the same way, and state statutes only bite under that state's law."""

import pytest
from pydantic import ValidationError

from conftest import NONCOMPETE_TERM, deal, make_law_pack, make_pack
from counselcopilot.policy.jurisdictions import is_jurisdiction, is_us, normalise_jurisdiction
from counselcopilot.policy.schema import (ConditionError, DealContext, FieldConstraint, PolicyPack, Rule,
                                          compile_condition, evaluate_condition)


def rule(**kw) -> Rule:
    return Rule(**{"id": "P-01", "title": "t", "requirement": "r", "kind": "require", **kw})


# ------------------------------------------------------------------ applicability conditions

@pytest.mark.parametrize("expr, d, expected", [
    ("True", deal(), True),
    ("counterparty == 'vendor'", deal(), True),
    ("counterparty == 'vendor'", deal(counterparty_type="customer"), False),
    ("counterparty in ['vendor', 'partner'] and personal_data", deal(personal_data=True), True),
    ("counterparty in ['vendor', 'partner'] and personal_data", deal(personal_data=False), False),
    ("not personal_data", deal(personal_data=False), True),
    ("foreign", deal(counterparty_country="GB"), True),
    ("foreign", deal(counterparty_country="US"), False),
    ("value_band == 'high' or counterparty == 'employee'", deal(counterparty_type="employee"), True),
    ("us_law", deal(governing_law="california"), True),
    ("us_law", deal(governing_law="united kingdom"), False),
    ("governing_law == 'california'", deal(governing_law="california"), True),
    ("company_side != 'receiving'", deal(), True),
])
def test_condition_over_deal_variables(expr, d, expected):
    assert evaluate_condition(expr, d) is expected


def test_empty_condition_means_always():
    assert evaluate_condition("", deal()) is True


@pytest.mark.parametrize("expr", [
    "__import__('os').system('echo hi')",  # calls
    "deal.company",                          # attribute access
    "counterparty[0] == 'v'",                # subscripts
    "len(counterparty) > 2",                 # comparisons other than == != in
    "lambda: True",
    "counterparty ==",                       # syntax error
])
def test_conditions_cannot_execute_code(expr):
    """Conditions come from LLM-compiled policies; they are parsed, never executed."""
    with pytest.raises(ConditionError):
        compile_condition(expr)


def test_unknown_deal_variable_is_an_error():
    with pytest.raises(ConditionError, match="unknown deal variable"):
        evaluate_condition("deal_size == 'big'", deal())


def test_rule_with_bad_condition_does_not_load():
    with pytest.raises(ValidationError):
        rule(applies_if="open('x')")


# ------------------------------------------------------------------ deal context

def test_inferable_facts_left_blank_are_reported():
    d = DealContext(company="X", counterparty_type="vendor", personal_data=None, governing_law=None)
    assert d.unknown_facts() == ["personal_data", "governing_law"]
    assert deal().unknown_facts() == []


def test_us_counterparty_written_out_is_not_foreign():
    assert deal(counterparty_country="United States").variables()["foreign"] is False


# ------------------------------------------------------------------ rules and packs

def test_rule_ids_follow_the_pack_format():
    rule(id="P-07")
    rule(id="LAW-CA-BPC-16600")
    with pytest.raises(ValidationError):
        rule(id="p7")


def test_field_rule_needs_a_constraint():
    with pytest.raises(ValidationError):
        rule(kind="field")


def test_check_term_falls_back_to_requirement():
    assert rule(requirement="must do X").check_term == "must do X"
    assert rule(requirement="must do X", term="The NDA does X.").check_term == "The NDA does X."


def test_rule_text_cites_source_and_approver():
    r = rule(approval="General Counsel", source={"document": "Policy", "quote": "We require X."})
    text = r.as_text()
    assert "[P-01]" in text and "General Counsel" in text and "We require X." in text


def test_pack_rejects_duplicate_ids():
    p = make_pack().rules[0].model_dump()
    with pytest.raises(ValidationError, match="duplicate"):
        PolicyPack(company="X", rules=[p, p])


def test_pack_rejects_dangling_cross_reference_but_allows_law_refs():
    base = make_pack().rules[1].model_dump()
    with pytest.raises(ValidationError, match="unknown rule"):
        PolicyPack(company="X", rules=[{**base, "refs": ["P-99"]}])
    PolicyPack(company="X", rules=[{**base, "refs": ["LAW-DTSA-1833B"]}])


def test_applicable_rules_depend_on_the_deal(pack):
    vendor = {r.id for r in pack.applicable(deal(counterparty_type="vendor", personal_data=True))}
    customer = {r.id for r in pack.applicable(deal(counterparty_type="customer", personal_data=False))}
    assert vendor == {"P-01", "P-02", "P-04", "P-05", "P-06"}
    assert customer == {"P-02", "P-03", "P-05", "P-06"}


def test_pack_rule_lookup(pack):
    assert pack.rule("P-05").approval == "General Counsel"
    with pytest.raises(KeyError):
        pack.rule("P-99")


@pytest.mark.parametrize("op, value, actual, ok", [
    (">=", 36, 48.0, True), (">=", 36, 12.0, False), ("<=", 60, 9999.0, False),
    ("in", ["delaware", "new york"], "delaware", True), ("in", ["delaware"], "california", False),
    ("not in", ["california"], "texas", True), ("==", True, True, True), ("!=", True, True, False),
])
def test_field_constraints(op, value, actual, ok):
    assert FieldConstraint(field="confidentiality_term_months", op=op, value=value).check(actual) is ok


def test_missing_field_value_never_satisfies_a_constraint():
    assert FieldConstraint(field="governing_law", op="not in", value=["california"]).check(None) is False


def test_load_pack_from_yaml(tmp_path, pack):
    import yaml

    f = tmp_path / "pack.yaml"
    f.write_text(yaml.safe_dump(pack.model_dump(mode="json")))
    assert PolicyPack.load(f).rule("P-04").constraint.value == 36


# ------------------------------------------------------------------ US law pack

def test_state_statute_applies_only_under_that_state_law():
    """Proposal §1: a non-compete is a risk under California law (Cal. B&P Code §16600)."""
    rules = {r.id: r for r in make_law_pack().as_rules()}
    ca = rules["LAW-CA-BPC-16600"]
    assert ca.applies_to(deal(governing_law="california"))
    assert not ca.applies_to(deal(governing_law="delaware"))
    assert not ca.applies_to(deal(governing_law="united kingdom"))


def test_us_wide_provision_applies_under_any_us_law_only():
    pen = {r.id: r for r in make_law_pack().as_rules()}["LAW-PENALTY"]
    assert pen.applies_to(deal(governing_law="texas"))
    assert pen.applies_to(deal(governing_law="united states"))
    assert not pen.applies_to(deal(governing_law="singapore"))


def test_federal_provision_combines_with_its_own_condition():
    dtsa = {r.id: r for r in make_law_pack().as_rules()}["LAW-DTSA-1833B"]
    assert dtsa.applies_to(deal(counterparty_type="employee", governing_law="singapore"))
    assert not dtsa.applies_to(deal(counterparty_type="vendor"))


def test_law_provisions_become_checkable_rules():
    rules = {r.id: r for r in make_law_pack().as_rules()}
    ca = rules["LAW-CA-BPC-16600"]
    assert ca.kind == "forbid" and ca.check_term == NONCOMPETE_TERM
    assert ca.source.document.startswith("California")  # findings cite the statute
    assert rules["LAW-DTSA-1833B"].kind == "require"


def test_unchecked_provisions_are_listed():
    """Proposal §6: each provision is checked by two teammates against the official text."""
    assert make_law_pack(checked=False).unchecked() == ["LAW-CA-BPC-16600", "LAW-DTSA-1833B", "LAW-PENALTY"]
    assert make_law_pack(checked=True).unchecked() == []


# ------------------------------------------------------------------ jurisdictions (USA, proposal §1)

@pytest.mark.parametrize("raw, norm", [
    ("the State of California", "california"), ("Commonwealth of Massachusetts", "massachusetts"),
    ("New York, without regard to conflicts", "new york"), ("Delaware and the federal laws", "delaware"),
    ("England and Wales", "united kingdom"), ("USA", "united states"), ("Province of Ontario", "canada"),
    ("Republic of Singapore", "singapore"),
])
def test_normalise_jurisdiction(raw, norm):
    assert normalise_jurisdiction(raw) == norm


def test_us_and_jurisdiction_predicates():
    assert is_us("texas") and is_us("united states")
    assert not is_us("united kingdom") and not is_us(None) and not is_us("unknown")
    assert is_jurisdiction("india") and is_jurisdiction("ohio")
    assert not is_jurisdiction("state") and not is_jurisdiction(None)
