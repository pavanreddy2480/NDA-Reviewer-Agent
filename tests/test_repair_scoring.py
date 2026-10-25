"""RQ2 scoring (proposal §3 H2, §4 Figure 3, §7 repair loop).

Redlines are the smallest clause-level edits. Final scores never use the loop's own checker:
an independent evaluator checks every applicable rule before and after repair, counts a fix or a
regression only when a second run confirms it, measures its own noise floor on unchanged drafts,
attributes regressions to individual redlines (H2: fewer than 5% of redlines introduce a new
violation) and is validated against ContractNLI expert labels and human labels (Cohen's kappa)."""

import json

import pytest

from conftest import NONSOLICIT_TERM, ORAL_TERM, RETURN_TERM, KeywordLLM, deal, make_doc, make_pack
from counselcopilot.data.draft import Draft, Edit
from counselcopilot.eval.evaluator import IndependentEvaluator, changed_segments, kappa_ci
from counselcopilot.llm import FakeClient

PACK = make_pack()


# ------------------------------------------------------------------ redlines

BASE = Draft("d", ["A.", "B.", "C."])


def test_replace_insert_delete():
    out = BASE.apply([Edit("replace", 1, "B2."), Edit("insert_after", 2, "D."), Edit("delete", 0)])
    assert out.segments == ["B2.", "C.", "D."]
    assert out.source_ids == [None, 2, None]
    assert BASE.segments == ["A.", "B.", "C."]  # the original draft is untouched


def test_insert_at_the_start():
    assert BASE.apply([Edit("insert_after", -1, "Z.")]).segments == ["Z.", "A.", "B.", "C."]


def test_edit_indices_refer_to_the_draft_before_editing():
    out = BASE.apply([Edit("insert_after", 0, "A2."), Edit("replace", 2, "C2.")])
    assert out.segments == ["A.", "A2.", "B.", "C2."]


def test_from_text_splits_lines_and_sentences():
    d = Draft.from_text("Definitions. Confidential Information means X.\n\nTerm; the term is two years.")
    assert d.segments == ["Definitions.", "Confidential Information means X.", "Term; the term is two years."]


def test_numbered_view():
    assert BASE.numbered([0, 2]) == "[0] A.\n[2] C."
    assert BASE.text == "A.\nB.\nC."


def test_from_nda_keeps_contractnli_spans():
    doc = make_doc(["First span.", "Second span."])
    d = Draft.from_nda(doc)
    assert d.id == "1" and d.segments == ["First span.", "Second span."] and d.source_ids == [0, 1]


def test_changed_segments_counts_edit_size():
    after = BASE.apply([Edit("replace", 1, "B2."), Edit("insert_after", 2, "D.")])
    assert changed_segments(BASE, after) == 2
    assert changed_segments(BASE, BASE) == 0


# ------------------------------------------------------------------ the independent evaluator

BEFORE = Draft("1", [
    "Confidential Information includes information disclosed orally.",
    "Neither party shall solicit the other's employees.",
    "The obligations last for four (4) years.",
    "This Agreement is governed by the laws of the State of Delaware.",
])
# the repair adds return/destroy (fixes P-01) but deletes the oral-disclosure clause (breaks P-02)
EDITS = [Edit("insert_after", 3, "The Receiving Party shall return or destroy Confidential Information."),
         Edit("delete", 0)]
AFTER = BEFORE.apply(EDITS)


def evaluator(**kw) -> IndependentEvaluator:
    return IndependentEvaluator(KeywordLLM(fields={"confidentiality_term_months": "four (4) years", "governing_law": "Delaware"},
                                           field_hints={"confidentiality_term_months": "years"}, **kw))


def test_evaluator_reads_the_whole_draft_with_its_own_prompt():
    ev = evaluator()
    st = ev.check(PACK.rule("P-02"), BEFORE)
    assert st.ok and st.result.label == "Entailment"
    prompt = ev.llm.requests[0].messages[-1].content
    assert prompt.startswith("CONTRACT TERM:") and all(f"[{i}]" in prompt for i in range(4))
    assert "auditing a revised contract" in ev.llm.requests[0].messages[0].content


def test_forbid_rule_is_ok_unless_entailed():
    ev = evaluator()
    assert not ev.check(PACK.rule("P-03"), BEFORE).ok
    assert ev.check(PACK.rule("P-03"), AFTER.apply([Edit("delete", 0)])).ok


def test_field_rules_are_scored_deterministically():
    ev = evaluator()
    assert ev.check(PACK.rule("P-06"), BEFORE).ok
    short = IndependentEvaluator(KeywordLLM(fields={"confidentiality_term_months": "perpetual"}))
    assert not short.check(PACK.rule("P-06"), BEFORE).ok


@pytest.mark.xfail(strict=True, reason="BUG: a field the evaluator finds left blank ('____ years') counts as "
                                        "satisfied, so a repairer could 'fix' a short term by blanking it")
def test_blanked_field_does_not_count_as_fixed():
    blank = IndependentEvaluator(KeywordLLM(fields={"confidentiality_term_months": "blank"}))
    assert not blank.check(PACK.rule("P-06"), BEFORE).ok


def test_score_repair_finds_fix_and_regression():
    out = evaluator().score_repair(BEFORE, AFTER, list(PACK.rules), deal(counterparty_type="vendor"))
    assert "P-01" in out["fixed"]
    assert out["regressions"] == ["P-02"]
    assert out["remaining"] == ["P-02"]
    assert out["n_rules"] == len(PACK.applicable(deal(counterparty_type="vendor")))
    assert out["edit_segments_changed"] == 1


def test_score_repair_only_checks_applicable_rules():
    out = evaluator().score_repair(BEFORE, BEFORE, list(PACK.rules), deal(counterparty_type="vendor"))
    assert out["fixed"] == [] and out["regressions"] == []
    assert out["remaining"] == ["P-01"]  # still no return clause; P-03 does not apply to vendors


class FlakyLLM(KeywordLLM):
    """The second-seed run (temperature 0.7) disagrees about everything: evaluator noise."""

    def _respond(self, req):
        out = super()._respond(req)
        if req.seed == 1 and '"label"' in out:
            d = json.loads(out)
            d["label"] = "NotMentioned" if d["label"] == "Entailment" else "Entailment"
            out = json.dumps(d)
        return out


def test_unconfirmed_flips_are_noise_not_fixes_or_regressions():
    ev = IndependentEvaluator(FlakyLLM())
    out = ev.score_repair(BEFORE, AFTER, [PACK.rule("P-01"), PACK.rule("P-02")], deal())
    assert out["fixed"] == [] and out["regressions"] == []
    assert "P-02" not in out["remaining"]  # an unconfirmed ok -> broken flip is not a remaining defect


def test_confirmation_run_uses_another_seed_and_temperature():
    ev = evaluator()
    ev.score_repair(BEFORE, AFTER, [PACK.rule("P-01")], deal())
    seeds = {(r.seed, r.temperature) for r in ev.llm.requests}
    assert seeds == {(0, 0.0), (1, 0.7)}


def test_regressions_are_attributed_to_the_redline_that_caused_them():
    blame = evaluator().attribute(BEFORE, EDITS, list(PACK.rules), ["P-02"])
    assert blame == {0: [], 1: ["P-02"]}
    rate = sum(bool(v) for v in blame.values()) / len(EDITS)  # H2: share of redlines that break a rule
    assert rate == 0.5


def test_noise_floor_is_zero_for_a_deterministic_judge_and_high_for_a_flaky_one():
    drafts = [BEFORE, AFTER.__class__("2", AFTER.segments)]
    deals = {"1": deal(), "2": deal()}
    assert evaluator().noise_floor(drafts, list(PACK.rules), deals)["flip_rate"] == 0.0
    flaky = IndependentEvaluator(FlakyLLM()).noise_floor(drafts, list(PACK.rules), deals)
    assert flaky["flip_rate"] == 1.0 and flaky["n"] > 0


def test_validation_on_contractnli_expert_labels():
    doc = make_doc(["Confidential Information includes information disclosed orally.", "Costs."],
                   labels={"nda-3": ("Entailment", (0,))})
    hyps = {h: f"hypothesis {h}" for h in doc.annotations}
    hyps["nda-3"] = ORAL_TERM
    out = evaluator().validate_on_contractnli([doc], hyps, n=100)
    assert out["n"] == len(doc.annotations) and out["agreement"] == 1.0 and out["kappa"] == 1.0


def test_validation_against_human_labels_reports_kappa_and_ci():
    out = IndependentEvaluator.validate([True, True, False, False], [True, False, False, False])
    assert out["agreement"] == 0.75 and out["kappa"] == 0.5
    assert len(out["kappa_ci95"]) == 2 and out["kappa_ci95"][0] <= out["kappa_ci95"][1]
    assert kappa_ci([], []) == [0.0, 0.0]


def test_evaluator_must_not_be_the_loop_checker_backend():
    """configs/backends.toml: the RQ2 judge is a role of its own, not a backbone."""
    from counselcopilot.llm.factory import roles

    r = roles()
    assert r["evaluator"] not in r["backbones"]
