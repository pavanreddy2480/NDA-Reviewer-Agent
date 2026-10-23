"""Tests for LLM-generated policy packs and two-model auto labels (no network)."""

import json
import re

import yaml

from counselcopilot.benchmark.autolabel import autolabel, label_accuracy, write_autolabels
from counselcopilot.benchmark.labels import load_labels
from counselcopilot.benchmark.packgen import PROFILES, PackGenerator, check_spec, import_pack, save_generated
from counselcopilot.data.contractnli import load_contractnli
from counselcopilot.llm import FakeClient
from counselcopilot.policy.schema import PolicyPack

from .conftest import HYPS, TOY_PACK

DOCS = PROFILES["saas"].documents


def _rules(n_total=30):
    hyps = list(HYPS)
    rules = []
    for i in range(n_total):
        r = {"id": f"P-{i + 1:02d}", "title": f"Rule {i + 1}", "requirement": f"Requirement {chr(65 + i)}.",
             "source": {"document": DOCS[i % len(DOCS)], "section": f"{i % 7 + 1}.1"}}
        if i < 18:  # anchored, at most two per hypothesis
            r.update(kind="forbid" if i in (0, 1, 16) else "require", anchor=hyps[i // 2])
        elif i < 26:  # field rules: governing law, then min/max pairs on three fields
            r.update(kind="field", constraint=[
                {"field": "governing_law", "op": "in", "value": ["delaware", "new york"]},
                {"field": "confidentiality_term_months", "op": ">=", "value": 24},
                {"field": "confidentiality_term_months", "op": "<=", "value": 60},
                {"field": "survival_months", "op": ">=", "value": 12},
                {"field": "survival_months", "op": "<=", "value": 60},
                {"field": "return_deadline_days", "op": ">=", "value": 5},
                {"field": "return_deadline_days", "op": "<=", "value": 30},
                {"field": "non_solicit_months", "op": "<=", "value": 12}][i - 18])
        else:
            r.update(kind="forbid", term=f"The NDA restricts thing {i}.")
        if i in (0, 1, 5, 9, 10, 13, 16, 20, 21, 23, 25, 27):
            r["applies_if"] = "personal_data and counterparty == 'vendor'" if i < 15 else "us_law"
        if i in (3, 7, 11, 18):
            r["approval"] = "General Counsel"
        if i in (4, 8, 12, 16, 20):
            r["refs"] = ["P-19"]
        rules.append(r)
    return rules


def _responder(req):
    sys_msg, msg = req.messages[0].content, req.messages[-1].content
    if "rule base" in sys_msg:
        first = not any(m.role == "assistant" for m in req.messages)
        return json.dumps({"rules": _rules(20 if first else 30)})  # first answer breaks the spec
    if "policy documents" in sys_msg:
        ids = re.findall(r"^- (P-\d+) \(section", msg, re.M)
        lines = ["# Policy", "Purpose and scope."] + [f"Clause {i}: staff must follow requirement {i}." for i in ids]
        return json.dumps({"markdown": "\n\n".join(lines), "quotes": {i: f"Clause {i}: staff must follow requirement {i}."
                                                                      for i in ids}})
    if "Does the passage state exactly" in msg:
        bad = "Requirement G." in msg
        return json.dumps({"matches": not bad, "problem": "wrong number" if bad else ""})
    raise AssertionError(msg[:200])


def test_spec_checker_rejects_toy_and_accepts_good_pack():
    assert check_spec(PolicyPack.load(TOY_PACK))
    good = PolicyPack.model_validate({"company": "X", "rules": [
        {**r, "anchor": {"hypothesis": r["anchor"]}} if "anchor" in r else r for r in _rules()]})
    assert check_spec(good, set(HYPS)) == []


def test_pack_generation_rules_first_then_prose(tmp_path):
    gen = PackGenerator(FakeClient(_responder), FakeClient(_responder), HYPS, ["nda-2"],
                        PolicyPack.load(TOY_PACK), target_words=2000)
    g = gen.generate(PROFILES["saas"], workers=1)
    assert len(g.pack.rules) == 30 and g.spec_problems == []
    assert any("rules round 0" in line for line in g.log) and any("rules round 1" in line for line in g.log)
    assert g.quote_problems == []
    for r in g.pack.rules:  # every gold rule is quoted verbatim from its own document
        assert r.source.quote in g.documents[r.source.document]
    assert set(g.flagged) == {"P-07"}
    out = save_generated(g, tmp_path, "fake", "fake")
    pack = PolicyPack.load(out / "gold_rules.yaml")
    assert len(pack.rules) == 30 and check_spec(pack) == []
    assert len(list((out / "policies").glob("*.md"))) == len(PROFILES["saas"].documents) + len(PROFILES["saas"].filler)
    review = (out / "REVIEW.md").read_text()
    assert "**P-07**: wrong number" in review and "Random spot check" in review
    again = import_pack(out, PROFILES["saas"], HYPS, "agent")  # a pack written outside packgen
    assert again.spec_problems == [] and again.quote_problems == []


def _labeller(law, term):
    def respond(req):
        return json.dumps({"is_template": False, "mutual": True, "parties": ["A", "B"], "disclosing_party": "A",
                           "governing_law": law, "personal_data": False, "confidentiality_term_months": term,
                           "survival_months": None, "return_deadline_days": None, "non_solicit_months": None,
                           "dispute_forum": "State of Delaware", "non_compete": False})
    return respond


def test_autolabel_agreement_and_disagreement(cnli_dir, tmp_path):
    docs = load_contractnli(cnli_dir)["test"]
    a = FakeClient(_labeller("Delaware", "three years"))
    b = FakeClient(_labeller("the State of Delaware", 36))
    labels = autolabel(docs, a, b, ("a", "b"), workers=1, sample_share=0.5)
    e = labels[docs[0].id]
    assert e["governing_law"] == "delaware" and e["company_party"] == "A"
    assert e["fields"]["confidentiality_term_months"] == 36.0  # "three years" and 36 agree
    assert e["fields"]["dispute_forum"] == "delaware"

    c = FakeClient(_labeller("california", 36))
    labels = autolabel(docs, a, c, ("a", "c"), workers=1, sample_share=0.0)
    e = labels[docs[0].id]
    assert e["governing_law"] == "disputed" and "governing_law" in e["auto"]["disagree"] and e["auto"]["needs_person"]

    path = tmp_path / "labels.yaml"
    write_autolabels(labels, path)
    loaded = load_labels(path, allow_auto=True)  # disputed keys stay "disputed" (unscored in gold)
    assert all(e["governing_law"] == "disputed" for e in loaded.values())
    raw = yaml.safe_load(path.read_text())
    raw[docs[0].id].update(verified=True, governing_law="delaware")
    path.write_text(yaml.safe_dump(raw))
    write_autolabels(autolabel(docs, a, c, ("a", "c"), workers=1), path)  # re-run keeps human work
    assert load_labels(path)[docs[0].id]["governing_law"] == "delaware"


def test_agreed_auto_labels_are_usable_and_audited(cnli_dir, tmp_path):
    docs = load_contractnli(cnli_dir)["test"]
    same = FakeClient(_labeller("delaware", 36))
    labels = autolabel(docs, same, same, ("a", "b"), workers=1, sample_share=0.5, seed=1)
    path = tmp_path / "labels.yaml"
    stats = write_autolabels(labels, path)
    assert stats["agreed"] == 2 and stats["need_person"] == 1
    assert len(load_labels(path, allow_auto=True)) == 2  # agreed entries are used; the audit measures them
    raw = yaml.safe_load(path.read_text())
    audited = next(k for k, v in raw.items() if v["auto"].get("audit"))
    raw[audited]["verified"] = True
    raw[audited]["auto"]["corrected"] = ["personal_data"]
    acc = label_accuracy({int(k): v for k, v in raw.items()})
    assert acc["audited_entries"] == 1 and 0.9 < acc["key_accuracy"] < 1


def test_labels_from_agent_answers(cnli_dir, tmp_path):
    from counselcopilot.benchmark.autolabel import autolabel_from_answers

    docs = load_contractnli(cnli_dir)["test"]
    raw = {"is_template": False, "mutual": True, "parties": ["A", "B"], "disclosing_party": "A",
           "governing_law": "Delaware", "personal_data": None, "confidentiality_term_months": "two years",
           "survival_months": None, "return_deadline_days": None, "non_solicit_months": None,
           "dispute_forum": None, "non_compete": False, "terms": {"X-1": True}}
    a = {d.id: raw for d in docs}
    b = {d.id: {**raw, "governing_law": None} for d in docs[:1]}
    labels = autolabel_from_answers(docs, a, b, ("s", "h"), sample_share=0.0, terms={"X-1": "a term"})
    e = labels[docs[0].id]
    assert set(labels) == {docs[0].id}
    assert e["governing_law"] == "disputed" and e["terms"]["X-1"] is True
    assert e["fields"]["confidentiality_term_months"] == 24.0
    path = tmp_path / "l.yaml"
    write_autolabels({999: {"verified": False}}, path)
    write_autolabels(labels, path)
    assert 999 in yaml.safe_load(path.read_text())  # other splits' entries are kept
