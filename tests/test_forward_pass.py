"""Forward-pass audit, 25 Oct 2026 (docs/reviews/forward-pass-audit.md).

One review, from the blank form to the findings, should read each fact once and use that one
reading everywhere, treat an unknown fact as unknown, and give B4 the whole NDA for every rule."""

import pytest

from conftest import COMPLIANT_SEGMENTS, KeywordLLM, make_law_pack, make_pack
from counselcopilot.data.draft import Draft
from counselcopilot.policy.schema import DealContext
from counselcopilot.review.policy_reviewer import PolicyReviewer, ReviewConfig

GOVERNED = "This Agreement is governed by the laws of the State of Delaware."


def blank_form(**kw) -> DealContext:
    return DealContext(**{"company": "TestCo", "counterparty_type": "vendor", "personal_data": False,
                          "governing_law": None, **kw})


def reviewer(main, checker=None, preset="full"):
    cfg = ReviewConfig.preset(preset)
    cfg.max_workers = 1
    return PolicyReviewer(main, make_pack(), cfg, law_pack=make_law_pack(), checker_llm=checker)


@pytest.mark.xfail(strict=True, reason="BUG: governing law is read twice, by the backbone for applicability "
                                        "(resolve_deal) and by the checker for the governing-law field rule; when "
                                        "they disagree the California statute applies while P-05 says Delaware is fine")
def test_governing_law_is_read_once_per_review():
    main = KeywordLLM(fields={"governing_law": "California"}, field_hints={"governing_law": "governed"}, name="backbone")
    checker = KeywordLLM(fields={"governing_law": "Delaware"}, field_hints={"governing_law": "governed"}, name="checker")
    reviewer(main, checker).review(Draft("d", list(COMPLIANT_SEGMENTS)), blank_form())
    asked = main.prompts_with("Which law governs") + checker.prompts_with("Which law governs")
    assert len(asked) == 1


def test_disagreeing_readings_give_an_inconsistent_review():
    """What the bug above does today: the deal says California, the field rule saw Delaware."""
    main = KeywordLLM(fields={"governing_law": "California"}, field_hints={"governing_law": "governed"}, name="backbone")
    checker = KeywordLLM(fields={"governing_law": "Delaware"}, field_hints={"governing_law": "governed"}, name="checker")
    res = reviewer(main, checker).review(Draft("d", list(COMPLIANT_SEGMENTS)), blank_form())
    assert res.deal.governing_law == "california" and "LAW-CA-BPC-16600" in res.rules_in_scope
    assert "P-05" not in {f.rule_id for f in res.findings}  # judged on "delaware"


@pytest.mark.xfail(strict=True, reason="BUG: when the personal-data question fails, the fact is left None and "
                                        "conditions read None as False, so every 'personal_data' rule is silently "
                                        "dropped from the review as if the NDA had no personal data")
def test_unreadable_personal_data_does_not_mean_no_personal_data():
    main = KeywordLLM(broken=True, name="backbone")
    checker = KeywordLLM(name="checker")
    res = reviewer(main, checker).review(Draft("d", list(COMPLIANT_SEGMENTS)),
                                         blank_form(personal_data=None, governing_law="delaware"))
    assert [f.value for f in res.inferred_facts if f.name == "personal_data"] == [None]
    assert "P-04" in res.rules_in_scope  # applies only with personal data


@pytest.mark.xfail(strict=True, reason="BUG: B4 'whole NDA in the prompt' only holds for term rules; field rules "
                                        "still extract from the top 6 retrieved segments in every preset")
def test_exhaustive_field_rules_see_the_whole_nda():
    segs = list(COMPLIANT_SEGMENTS) + [f"Clause {i} about notices and assignment." for i in range(8)]
    llm = KeywordLLM(fields={"governing_law": "Delaware", "confidentiality_term_months": 48},
                     field_hints={"governing_law": "governed"})
    reviewer(llm, preset="exhaustive_filtered").review(Draft("d", segs), blank_form(governing_law="delaware"))
    q = llm.prompts_with("How long do the confidentiality obligations last")[0].messages[-1].content
    assert all(f"[{i}]" in q for i in range(len(segs)))


def test_reverse_check_with_nothing_retrieved_is_an_omission_without_asking_the_model():
    """Documented, not a bug on its own: a require rule whose query matches no segment becomes an
    omission at confidence 1.0 with no model call, and still counts as one check."""
    pack = make_pack(rules=[{"id": "P-01", "title": "Escrow", "kind": "require", "requirement": "x",
                             "term": "Source code is deposited with an escrow agent.", "keywords": ["escrow"]}])
    llm = KeywordLLM()
    cfg = ReviewConfig.preset("reverse_only")
    cfg.max_workers = 1
    res = PolicyReviewer(llm, pack, cfg).review(Draft("d", list(COMPLIANT_SEGMENTS)),
                                                 blank_form(governing_law="delaware"))
    assert [(f.rule_id, f.type.value, f.confidence) for f in res.findings] == [("P-01", "omission", 1.0)]
    assert llm.check_requests() == [] and res.n_checks == 1
