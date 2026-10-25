"""Company policy packs (proposal §6): 3 fictional US companies, each with ~30 NDA rules buried in
~40k tokens of realistic prose; rules written first and prose second; about 60% of rules anchored
to ContractNLI's expert-labelled checks; anchored rules carry no numbers; a second model checks
the prose states each rule; the US law pack has 7 clear-cut provisions checked by two teammates.

These tests read the packs shipped in the repository (no ContractNLI download, no model)."""

import copy
import json
import shutil
from pathlib import Path

import pytest
import yaml

from conftest import make_pack
from counselcopilot.benchmark.packgen import (PROFILES, SPEC, PackGenerator, _quote_found, check_spec, import_pack)
from counselcopilot.benchmark.planter import LAW_TOPICS, load_library
from counselcopilot.data.contractnli import HELD_OUT_HYPOTHESES
from counselcopilot.llm import FakeClient
from counselcopilot.policy.schema import LawPack, PolicyPack

ROOT = Path(__file__).resolve().parents[1]
COMPANIES = ("saas", "hospital", "manufacturer")
HYPS = {f"nda-{i}" for i in (1, 2, 3, 4, 5, 7, 8, 10, 11, 12, 13, 15, 16, 17, 18, 19, 20)}


def shipped(company: str) -> PolicyPack:
    return PolicyPack.load(ROOT / "packs" / "policynda" / company / "gold_rules.yaml")


# ------------------------------------------------------------------ the spec checker

def test_small_pack_fails_the_spec_with_reasons():
    problems = check_spec(make_pack(), HYPS)
    assert any("rules; need" in p for p in problems)
    assert any("interacting" in p for p in problems)


def test_anchored_rules_must_not_carry_numbers():
    rules = [r.model_dump() for r in make_pack().rules]
    rules[0]["requirement"] = "Return our information within 30 days."
    problems = check_spec(PolicyPack(company="X", rules=rules), HYPS)
    assert any("P-01: anchored rules must not carry numbers" in p for p in problems)


def test_conditions_may_only_use_deal_variables():
    rules = [r.model_dump() for r in make_pack().rules]
    rules[1]["applies_if"] = "industry == 'health'"
    assert any("P-02: condition" in p for p in check_spec(PolicyPack(company="X", rules=rules), HYPS))


def test_unknown_anchor_is_reported():
    rules = [r.model_dump() for r in make_pack().rules]
    rules[1]["anchor"] = {"hypothesis": "nda-99"}
    assert any("unknown hypothesis nda-99" in p for p in check_spec(PolicyPack(company="X", rules=rules), HYPS))


def test_quotes_must_be_verbatim_up_to_whitespace():
    assert _quote_found("must  be\nreturned.", "All information must be returned. Then")
    assert not _quote_found("must be given back.", "All information must be returned.")
    assert not _quote_found("", "anything")


# ------------------------------------------------------------------ generation, rules first

def test_generator_sends_spec_problems_back_for_a_fix():
    good = {"rules": [r.model_dump(mode="json", exclude_none=True) for r in shipped("saas").rules]}
    bad = copy.deepcopy(good)
    bad["rules"] = bad["rules"][:10]
    replies = iter([bad, good])
    llm = FakeClient(lambda req: json.dumps(next(replies)))
    gen = PackGenerator(llm, None, {h: h for h in HYPS}, [], make_pack(), max_fix_rounds=2)
    pack = gen.rules(PROFILES["saas"])
    assert len(pack.rules) == 30 and len(llm.requests) == 2
    assert "Fix these problems" in llm.requests[1].messages[-1].content


def test_import_pack_reruns_spec_and_quote_checks(tmp_path):
    src = ROOT / "packs" / "policynda" / "saas"
    dst = tmp_path / "saas"
    shutil.copytree(src, dst)
    g = import_pack(dst, PROFILES["saas"], {h: h for h in HYPS}, generator="claude-sonnet (agent)")
    assert g.spec_problems == [] and g.quote_problems == []
    assert (dst / "REVIEW.md").exists() and "## 4. Anchors" in (dst / "REVIEW.md").read_text()


# ------------------------------------------------------------------ the shipped PolicyNDA packs

@pytest.mark.parametrize("company", COMPANIES)
def test_shipped_pack_meets_the_spec(company):
    assert check_spec(shipped(company), HYPS) == []


@pytest.mark.parametrize("company", COMPANIES)
def test_shipped_pack_shape_matches_the_proposal(company):
    pack = shipped(company)
    n = len(pack.rules)
    anchored = sum(r.anchor is not None for r in pack.rules) / n
    assert 26 <= n <= 34  # ~30 rules
    assert 0.5 <= anchored <= 0.7  # about 60% anchored
    assert pack.company == PROFILES[company].company


@pytest.mark.parametrize("company", COMPANIES)
def test_shipped_pack_is_about_forty_thousand_tokens_of_prose(company):
    words = sum(len(f.read_text().split()) for f in (ROOT / "packs" / "policynda" / company / "policies").glob("*.md"))
    assert 22_000 <= words <= 40_000  # ~0.75 words per token


@pytest.mark.parametrize("company", COMPANIES)
def test_every_rule_quotes_its_policy_text_verbatim(company):
    pack = shipped(company)
    docs = {f.stem: f.read_text() for f in (ROOT / "packs" / "policynda" / company / "policies").glob("*.md")}
    import re

    slug = lambda t: re.sub(r"[^a-z0-9]+", "_", t.lower()).strip("_")
    for r in pack.rules:
        assert r.source and r.source.quote, r.id
        assert _quote_found(r.source.quote, docs[slug(r.source.document)]), r.id


@pytest.mark.parametrize("company", COMPANIES)
def test_held_out_checks_are_used_by_the_packs(company):
    """Proposal §11: 5 checks are held out of fine-tuning and reported separately, so the packs
    must anchor rules to them."""
    anchors = {r.anchor.hypothesis for r in shipped(company).rules if r.anchor}
    assert set(HELD_OUT_HYPOTHESES) <= anchors


@pytest.mark.xfail(strict=True, reason="NOT DONE YET: proposal §6 says a teammate reviews flagged rules, every anchor "
                                        "and a random sample, but every REVIEW.md checklist is still unticked")
@pytest.mark.parametrize("company", COMPANIES)
def test_pack_review_checklist_is_complete(company):
    review = (ROOT / "packs" / "policynda" / company / "REVIEW.md").read_text()
    assert "- [ ]" not in review


# ------------------------------------------------------------------ the US law pack and clause library

def law_pack() -> LawPack:
    return LawPack.load(ROOT / "packs" / "law" / "us_law_pack.yaml")


def test_law_pack_has_the_seven_provisions_the_proposal_lists():
    ids = {p.id for p in law_pack().provisions}
    assert len(ids) == 7
    assert {"LAW-DTSA-1833B", "LAW-SEC-21F17", "LAW-SPEAK-OUT", "LAW-CA-BPC-16600",
            "LAW-CA-BPC-16600-NONSOLICIT", "LAW-PENALTY", "LAW-CCPA-SP"} == ids


def test_law_findings_are_worded_as_risk_with_sources():
    for p in law_pack().provisions:
        assert p.risk_level in ("risk", "possible_risk") and p.source_url.startswith("https://")


def test_california_statutes_only_apply_under_california_law():
    for p in law_pack().provisions:
        if "CA-BPC" in p.id:
            assert p.requires_law == ["california"]


@pytest.mark.xfail(strict=True, reason="NOT DONE YET: proposal §6 says each law provision is checked by two "
                                        "teammates against the official text; every checked_by list is empty")
def test_every_law_provision_is_checked_by_two_teammates():
    assert law_pack().unchecked() == []


def test_planter_has_a_clause_for_every_law_topic():
    topics = {c.topic for c in load_library()}
    ids = {p.id for p in law_pack().provisions}
    for rule_id, topic in LAW_TOPICS.items():
        assert rule_id in ids and topic in topics


def test_toy_pack_still_loads():
    toy = PolicyPack.load(ROOT / "packs" / "toy" / "toy_pack.yaml")
    assert toy.company == "ToyCo" and toy.rule("P-12").approval == "General Counsel"


def test_spec_constants_match_the_proposal():
    assert SPEC["n_rules"][0] <= 30 <= SPEC["n_rules"][1]
    assert SPEC["anchored_share"][0] <= 0.6 <= SPEC["anchored_share"][1]
