"""Two-model automatic NDA labels (replaces most hand labelling, 16 Oct 2026).

Two different LLMs read each whole NDA and fill the hand-label fields (benchmark/labels.py).
Where they agree, the label is accepted as `auto`; where they disagree, the entry is marked
for a person. A random share of the agreed entries is also sent to a person, so the report
can state how accurate agreed labels are (`label_accuracy`). Only the disagreements and that
sample need human time.

Disagreements are stored as "disputed", which benchmark/gold.py treats as unscored (never as
"absent from the NDA"). A governing law the NDA doesn't state is "none". `terms` labels say
whether the NDA contains the term of each unanchored require/forbid rule (law-pack provisions
such as the DTSA notice, and the packs' "other" rules), so those rules get natural gold.
"""

from __future__ import annotations

import random
from pathlib import Path

import yaml

from ..data.contractnli import NDADocument
from ..llm import LLMClient, system, user
from ..policy.jurisdictions import normalise_jurisdiction
from ..review.fields import BLANK, FIELD_QUESTIONS, _normalise
from .gold import DISPUTED, NO_LAW
from .labels import load_labels

LABEL_FIELDS = ["confidentiality_term_months", "survival_months", "return_deadline_days",
                "non_solicit_months", "dispute_forum", "non_compete"]
TOP_KEYS = ["is_template", "mutual", "governing_law", "personal_data", "disclosing_party"]

SCHEMA = {
    "type": "object",
    "properties": {
        "is_template": {"type": "boolean"},
        "mutual": {"type": "boolean"},
        "parties": {"type": "array", "items": {"type": "string"}},
        "disclosing_party": {"type": ["string", "null"]},
        "governing_law": {"type": ["string", "null"]},
        "personal_data": {"type": ["boolean", "null"]},
        **{f: {"type": ["string", "number", "boolean", "null"]} for f in LABEL_FIELDS},
    },
    "required": ["is_template", "mutual", "parties", "disclosing_party", "governing_law", "personal_data",
                 *LABEL_FIELDS],
}


def _prompt(doc: NDADocument, max_chars: int, terms: dict[str, str]) -> str:
    q = "\n".join(f"- {f}: {FIELD_QUESTIONS[f]}" for f in LABEL_FIELDS)
    t = ""
    if terms:
        t = ("- terms: an object; for each id below, true if the NDA contains this term (or something with "
             "the same effect), false if it does not:\n" + "\n".join(f"  {k}: {v}" for k, v in terms.items()) + "\n")
    return f"""Read this NDA and answer in JSON.
- is_template: true if it is a blank form with gaps such as "____", "[date]" or "[name]".
- mutual: true if both parties disclose and both are bound.
- parties: the names of the parties as written (or "Party A", "Party B" if blank).
- disclosing_party: for a one-way NDA, the party that discloses; for a mutual NDA, the first-named party.
- governing_law: {FIELD_QUESTIONS['governing_law']}
- personal_data: true if the NDA says personal data / personal information / customer or employee data may be
  shared, false if it clearly concerns only business or technical information, null if you cannot tell.
{q}
{t}If a template leaves a value blank, answer "blank".

NDA:
{doc.text[:max_chars]}"""


def ask(llm: LLMClient, doc: NDADocument, terms: dict[str, str] | None = None, max_chars: int = 60000) -> dict:
    terms = terms or {}
    schema = SCHEMA if not terms else {**SCHEMA, "properties": {**SCHEMA["properties"], "terms": {
        "type": "object", "properties": {k: {"type": "boolean"} for k in terms}}},
        "required": SCHEMA["required"] + ["terms"]}
    out = llm.complete_json([system("You label contracts precisely. Use only the document. Reply with JSON only."),
                             user(_prompt(doc, max_chars, terms))], schema, max_tokens=600 + 20 * len(terms),
                            tag="autolabel")
    return normalise_answer(out, terms)


def normalise_answer(out: dict, terms: dict[str, str] | None = None) -> dict:
    """One labeller's raw JSON answer (SCHEMA, plus `terms`) -> the form `merge` compares."""
    terms = terms or {}
    lab = {
        "is_template": bool(out.get("is_template")),
        "mutual": bool(out.get("mutual")),
        "disclosing_party": (out.get("disclosing_party") or None),
        "governing_law": normalise_jurisdiction(str(out["governing_law"])) if out.get("governing_law") else NO_LAW,
        "personal_data": out.get("personal_data") if isinstance(out.get("personal_data"), bool) else None,
        "fields": {},
    }
    for f in LABEL_FIELDS:
        v = out.get(f)
        lab["fields"][f] = BLANK if str(v).strip().lower() == BLANK else _normalise(f, v)
    got = out.get("terms") or {}
    lab["terms"] = {k: got.get(k) if isinstance(got.get(k), bool) else None for k in terms}
    return lab


def _same(a, b) -> bool:
    if isinstance(a, float) and isinstance(b, float):
        return abs(a - b) < 0.5
    if isinstance(a, str) and isinstance(b, str):
        return a.strip().lower() == b.strip().lower()
    return a == b


def merge(a: dict, b: dict, names: tuple[str, str]) -> dict:
    """One label entry from two models' answers. Disagreeing keys are left for a person."""
    entry = {"verified": False, "fields": {}}
    disagree = []
    for k in TOP_KEYS:
        if _same(a.get(k), b.get(k)):
            entry[k] = a.get(k)
        else:
            entry[k] = DISPUTED
            disagree.append(k)
    for f in LABEL_FIELDS:
        va, vb = a["fields"].get(f), b["fields"].get(f)
        if _same(va, vb):
            entry["fields"][f] = va
        else:
            disagree.append(f"fields.{f}")
            entry["fields"][f] = DISPUTED
    entry["terms"] = {}
    for t in sorted(set(a.get("terms", {})) | set(b.get("terms", {}))):
        va, vb = a.get("terms", {}).get(t), b.get("terms", {}).get(t)
        if isinstance(va, bool) and va == vb:
            entry["terms"][t] = va
        else:
            disagree.append(f"terms.{t}")
            entry["terms"][t] = DISPUTED
    entry["company_party"] = entry.pop("disclosing_party")  # the company is the disclosing side (deals.py)
    if "disclosing_party" in disagree:
        disagree[disagree.index("disclosing_party")] = "company_party"
    # unresolved values stay visible for the person who checks the entry
    entry["auto"] = {"by": list(names), "disagree": disagree,
                     "answers": {names[0]: {k: a.get(k) if k != "fields" else a["fields"] for k in a},
                                 names[1]: {k: b.get(k) if k != "fields" else b["fields"] for k in b}}
                     if disagree else {}}
    return entry


def autolabel(docs: list[NDADocument], llm_a: LLMClient, llm_b: LLMClient, names: tuple[str, str],
              workers: int = 8, sample_share: float = 0.2, seed: int = 0,
              terms: dict[str, str] | None = None) -> dict[int, dict]:
    """`terms`: rule id -> term, for the unanchored require/forbid rules (see rule_terms)."""
    ans_a = llm_a.map(lambda d: ask(llm_a, d, terms), docs, max_workers=workers)
    ans_b = llm_b.map(lambda d: ask(llm_b, d, terms), docs, max_workers=workers)
    out = {d.id: merge(a, b, names) for d, a, b in zip(docs, ans_a, ans_b)}
    agreed = sorted(i for i, e in out.items() if not e["auto"]["disagree"])
    k = round(sample_share * len(agreed))
    for i in random.Random(seed).sample(agreed, k):
        out[i]["auto"]["audit"] = True  # a person checks this agreed entry, to measure accuracy
    for i, e in out.items():
        e["auto"]["needs_person"] = bool(e["auto"]["disagree"]) or e["auto"].get("audit", False)
    return out


def autolabel_from_answers(docs: list[NDADocument], ans_a: dict[int, dict], ans_b: dict[int, dict],
                           names: tuple[str, str], sample_share: float = 0.2, seed: int = 0,
                           terms: dict[str, str] | None = None) -> dict[int, dict]:
    """Like `autolabel`, from answers written elsewhere (e.g. by Claude agents, 23 Oct 2026): raw JSON per doc id.
    A doc missing from either side is skipped."""
    ids = [d.id for d in docs if d.id in ans_a and d.id in ans_b]
    out = {i: merge(normalise_answer(ans_a[i], terms), normalise_answer(ans_b[i], terms), names) for i in ids}
    agreed = sorted(i for i, e in out.items() if not e["auto"]["disagree"])
    for i in random.Random(seed).sample(agreed, round(sample_share * len(agreed))):
        out[i]["auto"]["audit"] = True
    for e in out.values():
        e["auto"]["needs_person"] = bool(e["auto"]["disagree"]) or e["auto"].get("audit", False)
    return out


def write_autolabels(labels: dict[int, dict], path: str | Path) -> dict[str, int]:
    """Writes the label file; never overwrites an entry a person has verified."""
    path = Path(path)
    existing = load_labels(path, allow_unverified=True) if path.exists() else {}
    merged = {**existing,  # entries from another split stay
              **{i: (existing[i] if existing.get(i, {}).get("verified") else e) for i, e in labels.items()}}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(merged, sort_keys=True, allow_unicode=True))
    return {"entries": len(merged),
            "agreed": sum(not e.get("auto", {}).get("disagree") for e in merged.values()),
            "need_person": sum(e.get("auto", {}).get("needs_person", False) for e in merged.values())}


def label_accuracy(labels: dict[int, dict]) -> dict:
    """Accuracy of agreed auto labels on the audited entries, after a person has checked them.

    The checker sets `verified: true` and records any key they changed under `auto.corrected`."""
    audited = [e for e in labels.values() if e.get("auto", {}).get("audit") and e.get("verified")]
    keys = TOP_KEYS[:-1] + ["company_party"] + [f"fields.{f}" for f in LABEL_FIELDS]
    wrong = sum(len(e["auto"].get("corrected", [])) for e in audited)
    total = sum(len(keys) + len(e.get("terms", {})) for e in audited)
    return {"audited_entries": len(audited), "keys_checked": total,
            "key_accuracy": 1 - wrong / total if total else None,
            "entries_fully_correct": sum(not e["auto"].get("corrected") for e in audited)}



def term_key(company: str | None, rule_id: str) -> str:
    """Key of a `terms` label. Packs reuse ids (P-01 in every company), so pack rules are keyed
    "<company>:<id>"; law provisions (LAW-...) are shared by all companies."""
    return rule_id if rule_id.startswith("LAW-") or not company else f"{company}:{rule_id}"


def rule_terms(rules, company: str | None = None) -> dict[str, str]:
    """Term key -> term for rules that need a presence label: unanchored require/forbid rules."""
    return {term_key(company, r.id): r.check_term for r in rules
            if r.kind in ("require", "forbid") and r.anchor is None}
