import pytest

from counselcopilot.policy.schema import ConditionError, DealContext, PolicyPack, evaluate_condition

from .conftest import TOY_PACK


def deal(**kw):
    base = dict(company="ToyCo", counterparty_type="vendor")
    base.update(kw)
    return DealContext(**base)


def test_conditions():
    assert evaluate_condition("counterparty == 'vendor' and personal_data", deal(personal_data=True))
    assert not evaluate_condition("counterparty == 'vendor' and personal_data", deal())
    assert evaluate_condition("counterparty in ['vendor', 'partner']", deal())
    assert evaluate_condition("not foreign", deal())
    assert evaluate_condition("foreign", deal(counterparty_country="SG"))


@pytest.mark.parametrize("bad", ["__import__('os')", "a.b", "x + 1", "len(x)", "unknown_var"])
def test_conditions_reject_code(bad):
    with pytest.raises(ConditionError):
        evaluate_condition(bad, deal())


def test_toy_pack_applicability():
    pack = PolicyPack.load(TOY_PACK)
    vendor = {r.id for r in pack.applicable(deal())}
    customer = {r.id for r in pack.applicable(deal(counterparty_type="customer", personal_data=True))}
    assert "P-01" in vendor and "P-06" in vendor and "P-07" not in vendor and "P-11" not in vendor
    assert "P-07" in customer and "P-11" in customer and "P-01" not in customer


def test_pack_rejects_unknown_ref():
    with pytest.raises(ValueError):
        PolicyPack.model_validate({"company": "X", "rules": [
            {"id": "P-01", "title": "t", "requirement": "r", "kind": "require", "refs": ["P-99"]}]})
