"""LLM generation of the PolicyNDA company policy packs (replaces hand-writing, 16 Oct 2026).

Rules first, prose second, so the gold rule list is exact by construction:

1. **Rules.** One call writes the company's rule list in the PolicyPack format, to the
   targets in `docs/design/policy-pack-spec.md` (checked by `check_spec`). Problems are sent back for a
   fix, up to `max_fix_rounds` times.
2. **Prose.** Each policy document is written from the rules assigned to it, and must quote
   one sentence per rule verbatim (`source.quote`, checked here). Filler documents with no
   NDA rules pad the pack to the target size, as in a real company.
3. **Cross-check.** A second model reads each rule's quoted section and says whether the
   prose states exactly that rule (condition, number, approver). Disagreements go into
   REVIEW.md, so the human review covers only the flagged rules plus a sample.

Independence (design D17): the generator's prompts and outputs are never shown to the
reviewer. Use a different backend for generation than for the policy compiler, or report it.
"""

from __future__ import annotations

import json
import random
import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from ..llm import LLMClient, system, user
from ..llm.base import Message
from ..policy.schema import ConditionError, DealContext, FieldConstraint, PolicyPack, Rule, SourceRef

_SAMPLE_DEALS = [DealContext(company="X", counterparty_type=t, personal_data=pd, governing_law=gl,
                             counterparty_country=cc, company_side=side)
                 for t in ("vendor", "customer", "employee", "partner") for pd in (True, False)
                 for gl, cc, side in (("delaware", "US", "disclosing"), ("california", "GB", "mutual"))]
_NUMBERS = re.compile(r"\b\d+\b|\b(?:days?|months?|years?|one|two|three|four|five|six|seven|eight|nine|ten|"
                      r"eleven|twelve|fifteen|twenty|thirty|forty|fifty|sixty|ninety|hundred)\b", re.I)

# ---------------------------------------------------------------- spec (docs/design/policy-pack-spec.md)

SPEC = {
    "n_rules": (26, 34),
    "anchored_share": (0.50, 0.70),
    "field_share": (0.18, 0.32),
    "conditional_share": (0.35, 0.45),  # applies_if is not True
    "min_fact_conditions": 5,  # conditions that use personal_data, governing_law or us_law
    "min_forbid": 4,
    "approvals": (3, 5),
    "min_refs": 5,
    "max_governing_law_rules": 1,
    "min_interacting_pairs": 3,  # two field rules on one field, a minimum and a maximum (RQ2 interacting fixes)
    "min_cross_document_refs": 3,  # refs to a rule stated in another policy document (harder compilation)
    "min_distractor_rules": 3,  # conditional forbid rules the planter has a clause for (distractor-only NDAs)
}
FACT_VARS = ("personal_data", "governing_law", "us_law")
CONDITION_VARS = ("counterparty", "personal_data", "foreign", "value_band", "company_side",
                  "governing_law", "us_law", "counterparty_country")
FIELDS = list(FieldConstraint.model_fields["field"].annotation.__args__)


def _library_hypotheses() -> set[str]:
    from .planter import load_library

    return {h for c in load_library() for h in c.entails}


def check_spec(pack: PolicyPack, hypotheses: set[str] | None = None) -> list[str]:
    """Problems with a pack against docs/design/policy-pack-spec.md; empty list = meets the spec."""
    rules, n = pack.rules, len(pack.rules)
    out: list[str] = []

    def share(k: int) -> float:
        return k / n if n else 0.0

    lo, hi = SPEC["n_rules"]
    if not lo <= n <= hi:
        out.append(f"{n} rules; need {lo}-{hi}")
    for key, k, what in [
        ("anchored_share", sum(r.anchor is not None for r in rules), "anchored to a ContractNLI hypothesis"),
        ("field_share", sum(r.kind == "field" for r in rules), "field rules"),
        ("conditional_share", sum(r.applies_if.strip() != "True" for r in rules), "conditional (applies_if not True)"),
    ]:
        lo, hi = SPEC[key]
        if not lo <= share(k) <= hi:
            out.append(f"{k}/{n} rules {what} ({share(k):.0%}); need {lo:.0%}-{hi:.0%}")
    facts = sum(any(re.search(rf"\b{v}\b", r.applies_if) for v in FACT_VARS) for r in rules)
    if facts < SPEC["min_fact_conditions"]:
        out.append(f"{facts} conditions use {'/'.join(FACT_VARS)}; need at least {SPEC['min_fact_conditions']}")
    forbid = sum(r.kind == "forbid" for r in rules)
    if forbid < SPEC["min_forbid"]:
        out.append(f"{forbid} forbid rules; need at least {SPEC['min_forbid']}")
    lo, hi = SPEC["approvals"]
    appr = sum(bool(r.approval) for r in rules)
    if not lo <= appr <= hi:
        out.append(f"{appr} rules with an approval route; need {lo}-{hi}")
    refs = sum(bool(r.refs) for r in rules)
    if refs < SPEC["min_refs"]:
        out.append(f"{refs} rules with cross-references; need at least {SPEC['min_refs']}")
    gl = sum(r.kind == "field" and r.constraint.field == "governing_law" for r in rules)
    if gl > SPEC["max_governing_law_rules"]:
        out.append(f"{gl} governing-law rules; at most {SPEC['max_governing_law_rules']}")
    if hypotheses is not None:
        for r in rules:
            if r.anchor and r.anchor.hypothesis not in hypotheses:
                out.append(f"{r.id}: unknown hypothesis {r.anchor.hypothesis}")
    for r in rules:
        if r.anchor and r.kind == "field":
            out.append(f"{r.id}: field rules must not be anchored")
        if not r.source or not r.source.document:
            out.append(f"{r.id}: needs source.document (which policy document states it)")
        if r.kind == "forbid" and r.anchor is None and not r.term:
            out.append(f"{r.id}: unanchored forbid rules need a `term`")
    anchors = [r.anchor.hypothesis for r in rules if r.anchor]
    dup = sorted({h for h in anchors if anchors.count(h) > 2})
    if dup:
        out.append(f"more than two rules anchored to {dup}; spread anchors out")
    for r in rules:
        # conditions must only use deal variables, or gold raises later (audit 22 Oct)
        try:
            for d in _SAMPLE_DEALS:
                r.applies_to(d)
        except ConditionError as e:
            out.append(f"{r.id}: condition {r.applies_if!r} uses something other than {list(CONDITION_VARS)} ({e})")
        if r.kind == "field" and r.constraint.field == "governing_law" and not r.approval:
            out.append(f"{r.id}: the governing-law rule needs an approval route")
        # an anchored rule's gold is the ContractNLI label, which knows nothing about numbers;
        # "return within 30 days" anchored to nda-16 would mark a 90-day NDA compliant
        if r.anchor and (_NUMBERS.search(r.requirement) or _NUMBERS.search(r.term)):
            out.append(f"{r.id}: anchored rules must not carry numbers or durations; put them in a field rule")
    # a minimum and a maximum on the same field interact: a repair that fixes one can break the other
    fr = [r for r in rules if r.kind == "field" and r.constraint.op in (">=", "<=")]
    pairs = sum(1 for i, r in enumerate(fr) for q in fr[i + 1:]
                if q.constraint.field == r.constraint.field and q.constraint.op != r.constraint.op)
    if pairs < SPEC["min_interacting_pairs"]:
        out.append(f"{pairs} interacting min/max field-rule pairs; need at least {SPEC['min_interacting_pairs']}")
    # a distractor is a clause that breaks only a rule that does not apply; the planter can only
    # write one for a conditional forbid rule anchored to a hypothesis its library has a clause for
    lib = _library_hypotheses()
    dis = sum(r.kind == "forbid" and r.anchor is not None and r.anchor.hypothesis in lib
              and r.applies_if.strip() != "True" for r in rules)
    if dis < SPEC["min_distractor_rules"]:
        out.append(f"{dis} conditional forbid rules anchored to {sorted(lib)}; need at least "
                   f"{SPEC['min_distractor_rules']} (distractors)")
    doc_of = {r.id: (r.source.document if r.source else "") for r in rules}
    cross = sum(1 for r in rules for ref in r.refs if ref in doc_of and doc_of[ref] != doc_of[r.id])
    if cross < SPEC["min_cross_document_refs"]:
        out.append(f"{cross} cross-references to a rule in another document; need at least "
                   f"{SPEC['min_cross_document_refs']}")
    return out


# ---------------------------------------------------------------- companies

@dataclass
class CompanyProfile:
    slug: str
    company: str
    description: str
    documents: list[str]  # policy documents that state NDA rules
    filler: list[str]  # policy documents with no NDA rules (realistic padding)
    prefix: str = "P"


PROFILES = {
    "saas": CompanyProfile(
        "saas", "Northwind Cloud, Inc.",
        "Delaware-incorporated B2B SaaS company in New York. Vendor-heavy; customer personal data is common; "
        "sells to enterprises and some EU customers.",
        ["Confidentiality and NDA Standard", "Vendor and Third-Party Risk Policy", "Data Protection and Privacy Policy",
         "Contract Approval Matrix", "Intellectual Property Policy", "Records Retention and Disposal Policy"],
        ["Information Security Acceptable Use Policy", "Travel and Expense Policy", "Code of Business Conduct",
         "Open Source Software Policy", "Incident Response Policy"]),
    "hospital": CompanyProfile(
        "hospital", "Bayview Health Partners",
        "California non-profit hospital group. Patient data (PHI) is involved in most deals; HIPAA and CCPA apply; "
        "many vendors (IT, billing, research partners) and clinical staff.",
        ["Confidentiality Agreement Policy", "Business Associate and Vendor Policy", "Privacy and HIPAA Compliance Policy",
         "Delegation of Authority and Signature Policy", "Research Collaboration Policy", "Medical Records Retention Policy"],
        ["Patient Rights Policy", "Workplace Safety Policy", "Conflict of Interest Policy", "Social Media Policy",
         "Clinical Equipment Procurement Policy"]),
    "manufacturer": CompanyProfile(
        "manufacturer", "Keystone Precision Manufacturing, Inc.",
        "Ohio industrial manufacturer of precision components. IP-heavy (designs, processes, tooling); "
        "works with suppliers, distribution partners and engineers; little personal data.",
        ["Trade Secret Protection Policy", "Supplier Engagement Policy", "Partner and Distributor Policy",
         "Legal Review and Approval Policy", "Engineering Data Handling Policy", "Employee Confidentiality Policy"],
        ["Quality Management Policy", "Export Control Policy", "Environmental Health and Safety Policy",
         "Anti-Bribery Policy", "Capital Expenditure Policy"]),
}


# ---------------------------------------------------------------- prompts

RULES_SCHEMA = {
    "type": "object",
    "properties": {"rules": {"type": "array", "items": {"type": "object"}}},
    "required": ["rules"],
}

PROSE_SCHEMA = {
    "type": "object",
    "properties": {"markdown": {"type": "string"},
                   "quotes": {"type": "object", "additionalProperties": {"type": "string"}}},
    "required": ["markdown", "quotes"],
}

CROSSCHECK_SCHEMA = {
    "type": "object",
    "properties": {"matches": {"type": "boolean"}, "problem": {"type": "string"}},
    "required": ["matches", "problem"],
}


def _rules_prompt(p: CompanyProfile, hyps: dict[str, str], natural_violations: list[str], example: str) -> str:
    h = "\n".join(f"- {k}: {t}" for k, t in hyps.items())
    return f"""Write the NDA rule base of a fictional US company, as its legal team would apply it.

COMPANY: {p.company}. {p.description}
POLICY DOCUMENTS that state NDA rules (set source.document to one of these): {p.documents}

Each rule is one thing a consultant must get right when drafting an NDA for this company. Format: JSON
{{"rules": [...]}}; each rule has the fields of this YAML example (id, title, requirement, term, kind,
applies_if, severity, anchor, constraint, approval, refs, keywords, source):
{example}

Rules:
- ids {p.prefix}-01, {p.prefix}-02, ... in order.
- kind: "require" (the NDA must contain `term`), "forbid" (the NDA must not contain `term`), or "field"
  (a value in the NDA must meet `constraint`; fields: {FIELDS}; ops >=, <=, ==, !=, in, not in; months and
  days are numbers; governing_law values are lower-case US states).
- `term` is a statement about the NDA, worded like these ContractNLI hypotheses.
- anchor: {{"hypothesis": "nda-N"}} when the rule's term means the same as one of these hypotheses (a require
  rule anchored to H is met when the NDA entails H; a forbid rule anchored to H is broken when it entails H):
{h}
  These hypotheses have natural contradictions in real NDAs (good for require rules): {natural_violations}.
- applies_if: a condition over these variables only: {list(CONDITION_VARS)}. counterparty is one of
  'vendor', 'customer', 'employee', 'partner'; value_band is 'low', 'medium', 'high'; personal_data and
  us_law are booleans; governing_law is a lower-case US state. Python syntax with and/or/not/==/in, e.g.
  "counterparty in ['vendor', 'partner'] and personal_data". Use "True" for rules that always apply.
- source: {{"document": ..., "section": "4.2"}}. refs: ids of rules this one points to (e.g. an approval rule).

Targets (all must hold):
- {SPEC['n_rules'][0]}-{SPEC['n_rules'][1]} rules; about 60% anchored; about 25% field rules (never anchored);
- {SPEC['conditional_share'][0]:.0%}-{SPEC['conditional_share'][1]:.0%} of rules conditional (applies_if not "True");
- at least {SPEC['min_fact_conditions']} conditions use personal_data, governing_law or us_law;
- at least {SPEC['min_forbid']} forbid rules; {SPEC['approvals'][0]}-{SPEC['approvals'][1]} rules with an approval route;
- at least {SPEC['min_refs']} rules with refs; at most one governing-law rule, and it must have an approval route;
- no hypothesis anchored by more than two rules;
- anchored rules carry no numbers or durations (the ContractNLI label cannot check a number); put every
  number in a field rule;
- at least {SPEC['min_interacting_pairs']} pairs of field rules that set a minimum (>=) and a maximum (<=) on the same field
  (e.g. confidentiality term at least 24 and at most 60 months), so a repair can break one by fixing the other;
- at least {SPEC['min_cross_document_refs']} refs that point to a rule stated in a different policy document;
- at least {SPEC['min_distractor_rules']} conditional forbid rules (applies_if not "True", on counterparty or value_band) anchored to
  {sorted(_library_hypotheses())}.
Make the rules specific to this company's business, with realistic numbers and approvers."""


def _prose_prompt(p: CompanyProfile, doc: str, rules: list[Rule], words: int) -> str:
    if rules:
        listing = "\n".join(f"- {r.id} (section {r.source.section if r.source else '?'}): {r.requirement}"
                            + (f" Applies only when: {r.applies_if}." if r.applies_if.strip() != "True" else "")
                            + (f" Deviations need approval by {r.approval}." if r.approval else "")
                            for r in rules)
        task = f"""It must state each of these rules, in the section given, in the company's own words (do not
show the rule ids, and do not copy the wording above). State each rule's condition, numbers and approver
exactly; do not add rules about NDAs that are not listed.
{listing}

Return JSON {{"markdown": the whole document, "quotes": {{rule id: one sentence copied character for
character from the markdown that states that rule}}}}."""
    else:
        task = """It must not say anything about NDAs, confidentiality agreements or contract terms.

Return JSON {"markdown": the whole document, "quotes": {}}."""
    return f"""Write the "{doc}" of {p.company} ({p.description}).
Make it a realistic internal policy document of about {words} words: purpose, scope, definitions, numbered
sections, roles and responsibilities, procedures, exceptions, enforcement, revision history. Write in the style
of real US corporate policies.
{task}"""


def _crosscheck_prompt(rule: Rule, passage: str) -> str:
    return f"""A policy passage and a rule extracted from it. Does the passage state exactly this rule: the same
obligation, the same condition for when it applies, the same numbers and the same approver?

RULE: {rule.requirement}
APPLIES WHEN: {rule.applies_if}
APPROVER FOR DEVIATIONS: {rule.approval or "none"}

PASSAGE:
{passage}

Reply with JSON {{"matches": true or false, "problem": "" or what differs}}."""


# ---------------------------------------------------------------- generation

@dataclass
class GeneratedPack:
    profile: CompanyProfile
    pack: PolicyPack
    documents: dict[str, str] = field(default_factory=dict)  # title -> markdown
    spec_problems: list[str] = field(default_factory=list)
    quote_problems: list[str] = field(default_factory=list)
    flagged: dict[str, str] = field(default_factory=dict)  # rule id -> cross-check problem
    hypotheses: dict[str, str] = field(default_factory=dict)  # ContractNLI id -> text, for the anchor check
    log: list[str] = field(default_factory=list)

    @property
    def n_words(self) -> int:
        return sum(len(t.split()) for t in self.documents.values())


def _example_yaml(toy_pack: PolicyPack) -> str:
    keep = [toy_pack.rules[0]] + [r for r in toy_pack.rules if r.kind == "field"][:1]
    return yaml.safe_dump([r.model_dump(mode="json", exclude_none=True, exclude_defaults=True) for r in keep],
                          sort_keys=False)


def _parse_rules(raw: dict, company: str, description: str) -> PolicyPack:
    rules = []
    for r in raw.get("rules", []):
        r = {k: v for k, v in r.items() if v not in (None, "", [])}
        if isinstance(r.get("anchor"), str):
            r["anchor"] = {"hypothesis": r["anchor"]}
        rules.append(r)
    return PolicyPack.model_validate({"company": company, "description": description,
                                      "version": "gen-1", "rules": rules})


def _quote_found(quote: str, text: str) -> bool:
    norm = lambda s: re.sub(r"\s+", " ", s).strip()
    return bool(quote) and norm(quote) in norm(text)


def _passage(text: str, quote: str, chars: int = 1500) -> str:
    flat = re.sub(r"\s+", " ", text)
    i = flat.find(re.sub(r"\s+", " ", quote).strip())
    if i < 0:
        return flat[:chars]
    return flat[max(0, i - chars // 2): i + chars // 2]


class PackGenerator:
    def __init__(self, llm: LLMClient, checker: LLMClient | None, hypotheses: dict[str, str],
                 natural_violations: list[str], toy_pack: PolicyPack, max_fix_rounds: int = 3,
                 target_words: int = 30000, seed: int = 0):
        self.llm, self.checker = llm, checker
        self.hyps, self.natural = hypotheses, natural_violations
        self.example = _example_yaml(toy_pack)
        self.max_fix_rounds = max_fix_rounds
        self.target_words = target_words  # ~40k tokens
        self.rng = random.Random(seed)

    def rules(self, p: CompanyProfile, g: GeneratedPack | None = None) -> PolicyPack:
        msgs = [system("You are an in-house counsel writing a precise, machine-readable NDA rule base. Reply with JSON only."),
                user(_rules_prompt(p, self.hyps, self.natural, self.example))]
        pack, problems = None, ["no output"]
        for round_ in range(self.max_fix_rounds + 1):
            raw = self.llm.complete_json(msgs, RULES_SCHEMA, max_tokens=16000, temperature=0.7, tag="packgen_rules")
            try:
                pack = _parse_rules(raw, p.company, p.description)
                problems = check_spec(pack, set(self.hyps))
            except Exception as e:  # pydantic validation error: send it back
                problems = [f"invalid rule base: {str(e)[:1500]}"]
            if g is not None:
                g.log.append(f"rules round {round_}: {len(problems)} problems")
            if not problems:
                break
            msgs += [_assistant(json.dumps(raw)),
                     user("Fix these problems and return the whole rule base again as JSON:\n- " + "\n- ".join(problems))]
        if pack is None:
            raise RuntimeError(f"no valid rule base for {p.slug}: {problems}")
        if g is not None:
            g.spec_problems = problems
        return pack

    def document(self, p: CompanyProfile, title: str, rules: list[Rule], words: int) -> tuple[str, dict[str, str]]:
        msgs = [system("You write realistic internal corporate policy documents in Markdown. Reply with JSON only."),
                user(_prose_prompt(p, title, rules, words))]
        out = self.llm.complete_json(msgs, PROSE_SCHEMA, max_tokens=12000, temperature=0.7, tag="packgen_prose")
        text, quotes = out.get("markdown", ""), out.get("quotes", {}) or {}
        missing = [r.id for r in rules if not _quote_found(quotes.get(r.id, ""), text)]
        if missing:  # one repair round for quotes that are not verbatim
            msgs += [_assistant(json.dumps(out)),
                     user(f"These rules have no verbatim quote in the markdown: {missing}. Make sure the document "
                          "states them, and return the whole JSON again with exact quotes.")]
            out = self.llm.complete_json(msgs, PROSE_SCHEMA, max_tokens=12000, temperature=0.7, tag="packgen_prose")
            text, quotes = out.get("markdown", text), out.get("quotes", {}) or quotes
        return text, quotes

    def generate(self, p: CompanyProfile, workers: int = 4) -> GeneratedPack:
        g = GeneratedPack(p, PolicyPack(company=p.company, rules=[]), hypotheses=dict(self.hyps))
        pack = self.rules(p, g)
        by_doc: dict[str, list[Rule]] = {d: [] for d in p.documents}
        for r in pack.rules:
            doc = r.source.document if r.source and r.source.document in by_doc else self.rng.choice(p.documents)
            by_doc[doc].append(r)
        n_docs = len(p.documents) + len(p.filler)
        words = max(800, self.target_words // n_docs)
        jobs = [(d, by_doc[d]) for d in p.documents] + [(d, []) for d in p.filler]
        results = self.llm.map(lambda j: self.document(p, j[0], j[1], words), jobs, max_workers=workers)
        quotes: dict[str, str] = {}
        for (title, rules), (text, q) in zip(jobs, results):
            g.documents[title] = text
            for r in rules:
                if _quote_found(q.get(r.id, ""), text):
                    quotes[r.id] = q[r.id]
                else:
                    g.quote_problems.append(f"{r.id}: no verbatim quote in '{title}'")
        updated = []
        for r in pack.rules:
            src = r.source.model_dump() if r.source else {"document": ""}
            if r.id in quotes:
                src["quote"] = quotes[r.id]
            updated.append(r.model_copy(update={"source": SourceRef(**src)}))
        g.pack = pack.model_copy(update={"rules": updated})
        if self.checker is not None:
            self.crosscheck(g, workers)
        return g

    def crosscheck(self, g: GeneratedPack, workers: int = 4) -> None:
        rules = [r for r in g.pack.rules if r.source and r.source.quote]
        text_of = {r.id: g.documents.get(r.source.document, "") for r in rules}

        def one(r: Rule):
            return self.checker.complete_json(
                [user(_crosscheck_prompt(r, _passage(text_of[r.id], r.source.quote)))],
                CROSSCHECK_SCHEMA, max_tokens=300, tag="packgen_crosscheck")

        for r, out in zip(rules, self.checker.map(one, rules, max_workers=workers)):
            if not (out or {}).get("matches", False):
                g.flagged[r.id] = (out or {}).get("problem", "no answer")


def _assistant(text: str) -> Message:
    return Message("assistant", text)


# ---------------------------------------------------------------- output

def _slug(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", title.lower()).strip("_")


def save_generated(g: GeneratedPack, out_dir: str | Path, generator: str, checker: str | None) -> Path:
    out = Path(out_dir) / g.profile.slug
    (out / "policies").mkdir(parents=True, exist_ok=True)
    data = g.pack.model_dump(mode="json", exclude_none=True, exclude_defaults=True)
    data = {"company": g.pack.company, "description": g.pack.description, "version": g.pack.version, **data}
    header = (f"# GOLD rule list for {g.pack.company}, generated by {generator} (packgen.py) and reviewed by people.\n"
              "# Keep away from the reviewer builders: used only to score the policy compiler (design D17).\n")
    (out / "gold_rules.yaml").write_text(header + yaml.safe_dump(data, sort_keys=False, allow_unicode=True, width=110))
    for title, text in g.documents.items():
        (out / "policies" / f"{_slug(title)}.md").write_text(text)
    meta = {"generator": generator, "crosschecker": checker, "words": g.n_words, "log": g.log,
            "spec_problems": g.spec_problems, "quote_problems": g.quote_problems, "flagged": g.flagged}
    (out / "generation.json").write_text(json.dumps(meta, indent=1))
    (out / "REVIEW.md").write_text(review_checklist(g, generator, checker))
    return out


def import_pack(pack_dir: str | Path, p: CompanyProfile, hypotheses: dict[str, str], generator: str,
                checker: str | None = None, flagged: dict[str, str] | None = None) -> GeneratedPack:
    """A pack written outside packgen (e.g. by a Claude agent, 23 Oct 2026) in the save_generated layout:
    gold_rules.yaml plus policies/<slug>.md. Runs the same spec and verbatim-quote checks and rewrites REVIEW.md.
    `flagged`: rule id -> problem from a separate prose-vs-rule cross-check."""
    pack_dir = Path(pack_dir)
    pack = PolicyPack.load(pack_dir / "gold_rules.yaml")
    g = GeneratedPack(p, pack, hypotheses=dict(hypotheses), flagged=dict(flagged or {}))
    for title in p.documents + p.filler:
        f = pack_dir / "policies" / f"{_slug(title)}.md"
        if f.exists():
            g.documents[title] = f.read_text()
        else:
            g.quote_problems.append(f"missing policy file {f.name}")
    g.spec_problems = check_spec(pack, set(hypotheses))
    for r in pack.rules:
        doc = r.source.document if r.source else ""
        if doc not in p.documents:
            g.quote_problems.append(f"{r.id}: source.document {doc!r} is not one of the company's documents")
        elif not (r.source.quote and _quote_found(r.source.quote, g.documents.get(doc, ""))):
            g.quote_problems.append(f"{r.id}: no verbatim quote in '{doc}'")
    g.log.append(f"imported from {pack_dir}")
    save_generated(g, pack_dir.parent, generator, checker)
    return g


def review_checklist(g: GeneratedPack, generator: str, checker: str | None, sample: int = 6) -> str:
    flagged = sorted(g.flagged)
    rest = [r.id for r in g.pack.rules if r.id not in g.flagged]
    spot = sorted(random.Random(g.profile.slug).sample(rest, min(sample, len(rest))))
    lines = [f"# Review: {g.pack.company} policy pack", "",
             f"Generated by `{generator}`; cross-checked by `{checker or 'none'}`. "
             f"{len(g.pack.rules)} rules, {len(g.documents)} documents, about {g.n_words:,} words.", "",
             "Tick each box once you've checked it. Edit `gold_rules.yaml` or the policy file directly if something is "
             "wrong, then re-run `cc packs check`.", "",
             "## 1. Spec", ""]
    lines += [f"- [ ] {p}" for p in g.spec_problems] or ["- [x] meets docs/design/policy-pack-spec.md"]
    lines += ["", "## 2. Rules the cross-check flagged (prose and rule disagree)", ""]
    lines += [f"- [ ] **{i}**: {g.flagged[i]}" for i in flagged] or ["- none"]
    lines += ["", "## 3. Quotes not found in the prose", ""]
    lines += [f"- [ ] {q}" for q in g.quote_problems] or ["- none"]
    # gold for anchored rules is the ContractNLI label, so an anchor that does not mean the same as the
    # rule makes the gold wrong for every NDA (audit 22 Oct): a person checks each one
    lines += ["", "## 4. Anchors (does the rule mean the same as the hypothesis?)", ""]
    lines += [f"- [ ] **{r.id}** ({r.kind}): {r.requirement}  \n  ↔ {r.anchor.hypothesis}: "
              f"{g.hypotheses.get(r.anchor.hypothesis, '?')}" for r in g.pack.rules if r.anchor] or ["- none"]
    lines += ["", f"## 5. Random spot check ({len(spot)} rules the cross-check passed)", ""]
    lines += [f"- [ ] {i}" for i in spot]
    lines += ["", "## 6. Read-through", "",
              "- [ ] Skim each policy file: does it read like a real company policy, with no rule ids or AI phrasing?",
              "- [ ] Do the applicability conditions make business sense for this company?",
              "- [ ] Record the reviewer's name and the time spent here:", ""]
    return "\n".join(lines)
