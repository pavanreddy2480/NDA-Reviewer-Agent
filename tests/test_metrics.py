"""Evaluation plan (proposal §7): recall, precision and F1 per defect type; false alarms per NDA;
a finding counts only if both citations are correct (a rule-only score is also reported); natural
and planted defects reported separately; paired bootstrap 95% CIs over NDAs; TOST for the 3-point
margin; Cohen's kappa; ContractNLI accuracy and macro-F1; accuracy of deal facts read from the NDA."""

import pytest

from conftest import deal
from counselcopilot.benchmark.gold import GoldDefect, GoldNDA
from counselcopilot.eval.metrics import (PRF, bootstrap_ci, bootstrap_prf, cohen_kappa, evidence_recall,
                                         fact_accuracy, nli_metrics, paired_bootstrap, score_detection)
from counselcopilot.review.deal_facts import InferredFact
from counselcopilot.review.findings import Finding, FindingType

V, O, A = FindingType.VIOLATION, FindingType.OMISSION, FindingType.APPROVAL_NEEDED


def f(rule, t, ev=()):
    return Finding(draft_id="1", rule_id=rule, type=t, evidence=list(ev))


def g(defects, scored=(), unscored=(), doc_id=1):
    return GoldNDA(doc_id, deal(), [GoldDefect(*d) for d in defects], list(scored), list(unscored))


def overall(m):
    o = m["overall"]
    return o["tp"], o["fp"], o["fn"]


# ------------------------------------------------------------------ PRF

def test_prf_arithmetic_and_zero_division():
    p = PRF(tp=3, fp=1, fn=2)
    assert p.precision == 0.75 and p.recall == 0.6 and p.f1 == pytest.approx(2 * 0.75 * 0.6 / 1.35)
    assert PRF().precision == PRF().recall == PRF().f1 == 0.0


# ------------------------------------------------------------------ detection scoring

def test_true_positive_needs_rule_type_and_a_correct_clause_citation():
    gold = {1: g([("P-01", V, (4,))])}
    assert overall(score_detection({1: [f("P-01", V, (4, 5))]}, gold)) == (1, 0, 0)
    assert overall(score_detection({1: [f("P-01", V, (2,))]}, gold)) == (0, 1, 1)  # wrong clause
    assert overall(score_detection({1: [f("P-01", V, (2,))]}, gold, strict_citations=False)) == (1, 0, 0)


def test_omissions_need_no_clause_citation():
    assert overall(score_detection({1: [f("P-01", O)]}, {1: g([("P-01", O, ())])})) == (1, 0, 0)


def test_rule_only_score_ignores_the_type_but_reports_type_accuracy():
    gold = {1: g([("P-05", V, (3,))])}
    strict = score_detection({1: [f("P-05", A, (3,))]}, gold)
    lenient = score_detection({1: [f("P-05", A, (3,))]}, gold, lenient_type=True)
    assert overall(strict) == (0, 1, 1)
    assert overall(lenient) == (1, 0, 0) and lenient["type_accuracy"] == 0.0


def test_duplicate_predictions_count_once():
    m = score_detection({1: [f("P-01", O), f("P-01", O)]}, {1: g([("P-01", O, ())])})
    assert overall(m) == (1, 1, 0)


def test_flags_on_clean_or_non_applicable_rules_are_false_alarms():
    gold = {1: g([], scored=["P-01"]), 2: g([], doc_id=2)}
    m = score_detection({1: [f("P-01", O), f("P-03", V, (1,))], 2: [f("P-03", V)]}, gold)
    assert overall(m) == (0, 3, 0)
    assert m["false_alarms_per_nda"] == 1.5


def test_predictions_on_unscored_rules_are_ignored():
    gold = {1: g([], unscored=["P-04"])}
    assert overall(score_detection({1: [f("P-04", O)]}, gold)) == (0, 0, 0)
    assert overall(score_detection({1: [f("P-04", O)]}, gold, only_scored_rules=False)) == (0, 1, 0)


def test_natural_and_planted_are_scored_separately():
    gold = {1: g([("P-01", O, (), "natural"), ("P-02", O, (), "planted")])}
    preds = {1: [f("P-01", O), f("P-02", O)]}
    nat = score_detection(preds, gold, origin="natural")
    pla = score_detection(preds, gold, origin="planted")
    assert overall(nat) == (1, 0, 0) and overall(pla) == (1, 0, 0)  # the other origin is no false alarm
    assert nat["n_gold_defects"] == pla["n_gold_defects"] == 1
    assert overall(score_detection({1: []}, gold, origin="planted")) == (0, 0, 1)


def test_per_type_breakdown_and_evidence_count():
    gold = {1: g([("P-01", O, ()), ("P-02", V, (2,))])}
    m = score_detection({1: [f("P-01", O), f("P-09", V, (1,))]}, gold)
    assert m["by_type"]["omission"]["tp"] == 1
    assert m["by_type"]["violation"] == {**m["by_type"]["violation"], "tp": 0, "fp": 1, "fn": 1}
    assert m["n_gold_with_evidence"] == 1 and m["n_ndas"] == 1


def test_ndas_without_predictions_count_their_misses():
    m = score_detection({}, {1: g([("P-01", O, ())]), 2: g([("P-02", O, ())], doc_id=2)})
    assert overall(m) == (0, 0, 2) and m["per_doc"] == [(0, 0, 1), (0, 0, 1)]


# ------------------------------------------------------------------ confidence intervals and TOST

def test_bootstrap_ci_contains_the_point_estimate():
    per_doc = [(1, 0, 1), (2, 1, 0), (0, 1, 1), (3, 0, 0)] * 5
    ci = bootstrap_prf(per_doc)
    assert ci["recall"][0] <= 6 / 8 <= ci["recall"][1]
    assert bootstrap_prf([]) == {}


def test_bootstrap_is_seeded():
    per_doc = [(1, 0, 1), (2, 1, 0), (0, 1, 1)]
    assert bootstrap_prf(per_doc, seed=1) == bootstrap_prf(per_doc, seed=1)


def test_paired_bootstrap_detects_a_clear_gain():
    a = [(1, 0, 0)] * 30
    b = [(0, 0, 1)] * 30
    out = paired_bootstrap(a, b, "recall")
    assert out["diff"] == 1.0 and out["p_a_not_better"] == 0.0 and out["ci95"] == [1.0, 1.0]


def test_tost_equivalence_within_three_points():
    a = [(9, 0, 1)] * 20 + [(10, 0, 0)] * 20
    same = paired_bootstrap(a, list(a), "recall", margin=0.03)
    assert same["equivalent_within_margin"] and same["diff"] == 0.0
    worse = [(7, 0, 3)] * 40
    assert not paired_bootstrap(a, worse, "recall", margin=0.03)["equivalent_within_margin"]


def test_paired_bootstrap_needs_the_same_ndas():
    with pytest.raises(AssertionError):
        paired_bootstrap([(1, 0, 0)], [(1, 0, 0), (0, 0, 1)])


def test_bootstrap_ci_of_a_mean():
    lo, hi = bootstrap_ci([0, 1, 2, 3, 4] * 4)
    assert lo <= 2 <= hi
    assert bootstrap_ci([]) == (0.0, 0.0)


# ------------------------------------------------------------------ agreement

def test_cohen_kappa():
    assert cohen_kappa(["a", "b", "a", "b"], ["a", "b", "a", "b"]) == 1.0
    assert cohen_kappa(["a", "a", "b", "b"], ["a", "b", "a", "b"]) == 0.0
    assert cohen_kappa([True] * 4, [True] * 4) == 1.0
    assert cohen_kappa([], []) == 0.0
    with pytest.raises(ValueError):
        cohen_kappa(["a"], ["a", "b"])


# ------------------------------------------------------------------ ContractNLI metrics

def test_nli_metrics_macro_f1_over_labels_present_in_gold():
    gold = ["Entailment", "Entailment", "NotMentioned", "NotMentioned"]
    pred = ["Entailment", "NotMentioned", "NotMentioned", "Contradiction"]
    m = nli_metrics(gold, pred)
    assert m["accuracy"] == 0.5
    assert m["macro_f1"] == pytest.approx((2 / 3 + 0.5) / 2, abs=1e-4)  # Contradiction absent from gold
    assert m["confusion"]["Entailment->NotMentioned"] == 1 and m["n"] == 4


def test_evidence_recall_is_the_retrieval_ceiling():
    assert evidence_recall([(1, 2), (5,), ()], [[2, 3], [1], [0]]) == 0.5


# ------------------------------------------------------------------ deal facts read from the NDA

def test_fact_accuracy_against_labels():
    inferred = {1: [InferredFact("governing_law", "delaware", []), InferredFact("personal_data", True, [])],
                2: [InferredFact("governing_law", "unknown", []), InferredFact("personal_data", False, [])],
                3: [InferredFact("governing_law", "texas", [])]}
    labels = {1: {"governing_law": "State of Delaware", "personal_data": True},
              2: {"governing_law": "none", "personal_data": True},  # "the NDA doesn't say" is a value
              3: {"governing_law": "disputed"}}  # skipped
    acc = fact_accuracy(inferred, labels)
    assert acc["governing_law"] == {"accuracy": 1.0, "n": 2}
    assert acc["personal_data"] == {"accuracy": 0.5, "n": 2}
