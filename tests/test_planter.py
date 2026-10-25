"""Planted defects (proposal §6): violations, omissions, approval-gated deviations, statutory
risks and distractors, 2-4 per NDA; a planted edit may not break any other rule; about 25% of NDAs
get only distractors; 20 NDAs get prompt-injection text, which changes no gold; a loophole is planted
in half of the test NDAs; gold repairs are the original clauses behind planted defects."""

import random

import pytest

from conftest import COMPLIANT_SEGMENTS, deal, make_doc, make_law_pack, make_pack
from counselcopilot.benchmark.gold import gold_for
from counselcopilot.benchmark.planter import INJECTIONS, Planter, PlantedNDA, load_library, plant_split
from counselcopilot.review.findings import FindingType

PACK = make_pack()
LAW = make_law_pack()
# a compliant NDA: return/destroy (nda-16) and oral disclosures (nda-3) are there
NLI = {"nda-16": ("Entailment", (2,)), "nda-3": ("Entailment", (1,)), "nda-19": ("Entailment", (3,))}


def planter() -> Planter:
    return Planter(PACK, LAW)


def doc(i: int = 1):
    return make_doc(doc_id=i, labels=NLI)


LABELS = {"governing_law": "delaware", "fields": {"confidentiality_term_months": 48}}


def plant(seed=0, d=None, **kw):
    return planter().plant(doc(), d or deal(governing_law=None), random.Random(seed), labels=LABELS, **kw)


def keys(defects) -> set[tuple[str, str]]:
    return {(x.rule_id, x.type.value) for x in defects}


# ------------------------------------------------------------------ the clause library

def test_library_clauses_say_what_they_entail():
    lib = load_library()
    assert {c.topic for c in lib} >= {"non_solicit", "non_compete", "residuals", "penalty", "governing_law_state"}
    for c in lib:
        assert all(h.startswith("nda-") for h in c.entails)


def test_planted_loopholes_are_residuals_or_unlimited_carve_outs():
    loopholes = {c.topic for c in load_library() if c.loophole}
    assert "residuals" in loopholes and loopholes <= {"residuals", "independent_development", "technical_only"}


# ------------------------------------------------------------------ single operations

def test_planted_omission_deletes_the_clause_and_keeps_it_as_gold_repair():
    p = planter()
    from counselcopilot.benchmark.planter import _Work

    w = _Work(doc(), deal(), random.Random(0))
    assert p.plant_omission(w, PACK.rule("P-01"))
    out = w.finish()
    assert COMPLIANT_SEGMENTS[2] not in out.draft.segments
    assert keys(out.defects) == {("P-01", "omission")}
    assert out.gold_repairs[0]["kind"] == "reinsert" and out.gold_repairs[0]["original"] == [COMPLIANT_SEGMENTS[2]]
    assert out.edited


def test_omission_is_only_planted_where_the_original_satisfies_the_rule():
    from counselcopilot.benchmark.planter import _Work

    d = make_doc(labels={"nda-16": ("NotMentioned", ())})
    assert not planter().plant_omission(_Work(d, deal(), random.Random(0)), PACK.rule("P-01"))


def test_planted_omission_is_scored_as_planted():
    out = plant(n_defects=4)
    g = gold_for(doc(), out.deal, PACK, {**LABELS, **out.label_updates}, LAW, out.gold_entry())
    planted = {d.rule_id for d in g.defects if d.origin == "planted"}
    assert planted == {d.rule_id for d in out.defects}
    assert planted and all(d.origin == "planted" for d in out.defects)


def test_governing_law_violation_replaces_the_clause_and_records_the_repair():
    from counselcopilot.benchmark.planter import _Work

    w = _Work(doc(), deal(governing_law=None), random.Random(0))
    assert planter().plant_field_violation(w, PACK.rule("P-05"), LABELS)
    out = w.finish()
    assert keys(out.defects) == {("P-05", "approval_needed")}
    assert out.label_updates["governing_law"] not in ("delaware", "new york")
    new_seg = out.draft.segments[out.defects[0].evidence[0]]
    assert "Delaware" not in new_seg and out.gold_repairs[0]["original"] == [COMPLIANT_SEGMENTS[4]]


def test_violation_insert_is_new_text_cited_as_evidence():
    from counselcopilot.benchmark.planter import _Work

    w = _Work(doc(), deal(counterparty_type="customer"), random.Random(0))
    assert planter().plant_forbidden_clause(w, PACK.rule("P-03"), deal(counterparty_type="customer"))
    out = w.finish()
    d = out.defects[0]
    assert (d.rule_id, d.type) == ("P-03", FindingType.VIOLATION)
    assert "solicit" in out.draft.segments[d.evidence[0]]
    assert out.draft.source_ids[d.evidence[0]] is None
    assert out.overrides["nda-18"][0] == "Entailment"


def test_forbidden_clause_is_not_planted_if_already_present():
    from counselcopilot.benchmark.planter import _Work

    d = make_doc(labels={**NLI, "nda-18": ("Entailment", (5,))})
    w = _Work(d, deal(counterparty_type="customer"), random.Random(0))
    assert not planter().plant_forbidden_clause(w, PACK.rule("P-03"), deal(counterparty_type="customer"))


# ------------------------------------------------------------------ distractors

def test_distractor_breaks_only_a_rule_that_does_not_apply():
    out = plant(distractor_only=True, d=deal(counterparty_type="vendor"))
    assert out.defects == []
    lines = [line for line in out.log if line.startswith("distractor")]
    assert len(lines) == 1
    target = lines[0].split(" breaks ")[1].split(",")[0]
    g = gold_for(doc(), out.deal, PACK, {**LABELS, **out.label_updates}, LAW, out.gold_entry())
    assert target in g.not_applicable
    assert not any(d.origin == "planted" for d in g.defects)


def test_planted_edits_break_no_other_applicable_rule():
    """Every inserted library clause hits only its own target or rules that do not apply."""
    p = planter()
    lib = {c.text: c for c in load_library()}
    for seed in range(15):
        out = plant(seed=seed, n_defects=4, loophole=True)
        g = gold_for(doc(), out.deal, PACK, {**LABELS, **out.label_updates}, LAW, out.gold_entry())
        targets = {d.rule_id for d in out.defects}
        for i, seg in enumerate(out.draft.segments):
            clause = lib.get(seg)
            if clause is None or out.draft.source_ids[i] is not None:
                continue
            for r in list(PACK.rules) + LAW.as_rules():
                if p._clause_hits(clause, r):
                    assert r.id in targets or r.id in g.not_applicable, (seed, clause.id, r.id)


# ------------------------------------------------------------------ state law, loopholes, injection

def test_state_law_switch_makes_state_statutes_apply():
    out = plant(state_law="California", n_defects=0)
    assert out.label_updates["governing_law"] == "california"
    assert out.deal.governing_law is None  # the reviewer must read it from the NDA
    text = " ".join(out.draft.segments)
    assert "State of California" in text and "State of Delaware" not in text
    g = gold_for(doc(), out.deal, PACK, {**LABELS, **out.label_updates}, LAW, out.gold_entry())
    assert "LAW-CA-BPC-16600" not in g.not_applicable


def test_state_law_inserts_a_clause_when_the_nda_names_none():
    segs = [s for s in COMPLIANT_SEGMENTS if "governed" not in s]
    out = planter().plant(make_doc(segs, labels=NLI), deal(governing_law=None), random.Random(0),
                          n_defects=0, state_law="California")
    assert any("State of California" in s for s in out.draft.segments)


def test_planted_loophole_is_located_in_the_draft():
    out = plant(loophole=True, n_defects=0)
    planted = [lh for lh in out.loopholes if lh.get("origin") == "planted"]
    assert len(planted) == 1 and planted[0]["evidence"]
    assert out.draft.source_ids[planted[0]["evidence"][0]] is None


def test_natural_loopholes_follow_contractnli_labels_from_the_companys_side():
    d = make_doc(labels={**NLI, "nda-2": ("Entailment", (1,)), "nda-3": ("Contradiction", (1,))})
    out = planter().plant(d, deal(), random.Random(0), n_defects=0)
    assert {lh["hypothesis"] for lh in out.loopholes if lh["origin"] == "natural"} == {"nda-2", "nda-3"}
    recv = planter().plant(d, deal(company_side="receiving"), random.Random(0), n_defects=0)
    assert not [lh for lh in recv.loopholes if lh["origin"] == "natural"]


def test_standard_carve_outs_are_not_natural_loopholes():
    d = make_doc(labels={**NLI, "nda-12": ("Entailment", (5,)), "nda-13": ("Entailment", (5,))})
    out = planter().plant(d, deal(), random.Random(0), n_defects=0)
    assert not [lh for lh in out.loopholes if lh.get("hypothesis") in ("nda-12", "nda-13")]


def test_injection_text_changes_no_gold():
    a = plant(seed=4, n_defects=3)
    b = plant(seed=4, n_defects=3, injection=True)
    assert keys(a.defects) == keys(b.defects)
    assert b.injection["text"] in INJECTIONS
    assert [b.draft.segments[i] for i in b.injection["evidence"]] == [b.injection["text"]]
    ga = gold_for(doc(), a.deal, PACK, {**LABELS, **a.label_updates}, LAW, a.gold_entry())
    gb = gold_for(doc(), b.deal, PACK, {**LABELS, **b.label_updates}, LAW, b.gold_entry())
    assert keys(ga.defects) == keys(gb.defects)


def test_planting_is_deterministic_and_round_trips_through_json():
    a, b = plant(seed=9, loophole=True, injection=True), plant(seed=9, loophole=True, injection=True)
    assert a.to_json() == b.to_json()
    back = PlantedNDA.from_json(a.to_json())
    assert back.to_json() == a.to_json()
    assert back.draft.segments == a.draft.segments and keys(back.defects) == keys(a.defects)


# ------------------------------------------------------------------ a whole split

@pytest.fixture(scope="module")
def split():
    docs = [make_doc(doc_id=i, labels=NLI) for i in range(1, 81)]
    deals = {d.id: deal(counterparty_type=["vendor", "customer", "partner", "employee"][d.id % 4],
                        governing_law=None) for d in docs}
    out = plant_split({"TestCo": Planter(PACK, LAW)}, docs, deals, {d.id: LABELS for d in docs},
                      seed=0, n_state_law=30, n_injection=20)
    return docs, out


def test_split_sizes_follow_the_proposal(split):
    docs, out = split
    assert len(out) == len(docs)
    assert sum(bool(p.injection) for p in out) == 20
    assert sum(p.label_updates.get("governing_law") == "california" for p in out) >= 30 - 5  # minus law violations
    assert all(len(p.defects) <= 4 for p in out)


def test_about_a_quarter_are_distractor_only(split):
    _, out = split
    clean = sum(not p.defects for p in out) / len(out)
    assert 0.15 <= clean <= 0.45


def test_about_half_get_a_planted_loophole(split):
    _, out = split
    share = sum(any(lh.get("origin") == "planted" for lh in p.loopholes) for p in out) / len(out)
    assert 0.3 <= share <= 0.7
