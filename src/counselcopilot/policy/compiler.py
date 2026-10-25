"""Policy compiler: a company's prose policies -> requirement cards (proposal §4; design D17).

Offline, an LLM reads each policy document and writes one card per requirement the company
places on the NDAs it signs. A card is a `Rule` with:

- the statement the checker tests for (`term`) and its kind (require / forbid / field);
- `applies_when`, when the card applies in the policy's own words. The reviewer's model judges it
  against the deal and the NDA (review/applicability.py). The compiler also writes the structured
  `applies_if` over the deal variables when it can, so the structured filter stays as an ablation
  on the same cards;
- the document, section and verbatim quote it came from. A card whose quote is not in the
  document is dropped, so the compiler cannot invent policy.

Cards get ids C-01, C-02, ... . They are scored against the pack's gold rule list (which the
compiler never sees) by matching quotes (benchmark/align.py).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from ..llm import LLMClient, PendingBatch, system, user
from .schema import ConditionError, FieldConstraint, PolicyPack, Rule, compile_condition

FIELDS = list(FieldConstraint.model_fields["field"].annotation.__args__)
VARIABLES = ("counterparty ('vendor', 'customer', 'partner', 'employee'), personal_data (true/false), "
             "foreign (counterparty outside the US), value_band ('low', 'medium', 'high'), "
             "company_side ('disclosing', 'receiving', 'mutual'), governing_law (US state or country, "
             "lower case), us_law (true/false)")

CARD = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "kind": {"type": "string", "enum": ["require", "forbid", "field"]},
        "statement": {"type": "string"},
        "applies_when": {"type": "string"},
        "applies_if": {"type": "string"},
        "field": {"type": ["string", "null"]},
        "op": {"type": ["string", "null"]},
        "value": {},
        "severity": {"type": "string", "enum": ["low", "medium", "high"]},
        "approval": {"type": ["string", "null"]},
        "section": {"type": "string"},
        "quote": {"type": "string"},
        "keywords": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["title", "kind", "statement", "applies_when", "applies_if", "severity", "section", "quote"],
}
CARDS_SCHEMA = {"type": "object", "properties": {"cards": {"type": "array", "items": CARD}}, "required": ["cards"]}

COMPILER_SYSTEM = f"""You turn a company's internal policy into requirement cards for reviewing the NDAs (non-disclosure agreements) it signs.

Write one card for every requirement this document places on the *text of an NDA*: something an NDA must contain, must not contain, or a value it must have (a term length, a governing law, a deadline). Skip duties on staff that no NDA clause could meet (training, filing, who signs) unless they say who must approve a deviation; then put that person in "approval" on the card the deviation is about. Write no card for a document that has no such requirement.

Each card:
- "kind": "require" (the NDA must say it), "forbid" (the NDA must not say it) or "field" (a value with a limit).
- "statement": the NDA term, written as a statement about the NDA ("The Receiving Party must return or destroy Confidential Information on request."). For "forbid", state the clause that is not allowed. No numbers in require/forbid statements; put numeric limits in a field card.
- "applies_when": when the card applies, in plain words taken from the policy ("vendor NDAs where personal data is shared"); "always" if the policy sets no condition.
- "applies_if": the same condition over these deal variables: {VARIABLES}. Use only ==, !=, in, not in, and, or, not, e.g. "counterparty == 'vendor' and personal_data". "True" if always. "" if the condition can't be written with these variables.
- field cards only: "field" one of {FIELDS}; "op" one of >=, <=, ==, !=, in, not in; "value" a number (months or days as the field name says, 9999 for perpetual), a boolean, or a list of lower-case jurisdictions.
- "severity": how the policy ranks it (default "medium"); "approval": who may approve a deviation, or null.
- "section" and "quote": the section number and a verbatim sentence from the document that states the requirement. Copy it exactly.
- "keywords": 2 to 5 words an NDA clause on this would use.

Reply with JSON {{"cards": [...]}}."""


@dataclass
class CompileReport:
    documents: int = 0
    cards: int = 0
    dropped_quote: list[str] = field(default_factory=list)  # titles of cards whose quote wasn't found
    dropped_invalid: list[str] = field(default_factory=list)  # malformed cards
    unstructured: list[str] = field(default_factory=list)  # applies_if could not be written: "True"
    pending: list[str] = field(default_factory=list)  # documents waiting on the batch queue


def _norm(s: str) -> str:
    return re.sub(r"[\s*_`]+", " ", s).strip().lower()


def quote_found(quote: str, text: str) -> bool:
    """Whitespace- and markdown-insensitive containment; quotes shorter than 20 characters don't count."""
    q = _norm(quote)
    return len(q) >= 20 and q in _norm(text)


def _title(path: Path, text: str) -> str:
    m = re.search(r"^#\s+(.+)$", text, re.M)
    return m.group(1).strip() if m else path.stem.replace("_", " ").title()


def _card_to_rule(card: dict, rid: str, document: str, report: CompileReport) -> Rule | None:
    when = str(card.get("applies_when") or "").strip()
    expr = str(card.get("applies_if") or "").strip() or "True"
    try:
        compile_condition(expr)
    except ConditionError:
        expr = ""
    if not expr:
        report.unstructured.append(card.get("title", rid))
        expr = "True"
    rule = {
        "id": rid, "title": card.get("title") or rid, "kind": card.get("kind"),
        "requirement": card.get("statement", ""), "term": card.get("statement", ""),
        "applies_if": expr, "applies_when": "" if when.lower() in ("", "always") else when,
        "severity": card.get("severity") or "medium", "approval": card.get("approval") or None,
        "keywords": [str(k) for k in card.get("keywords") or []][:5],
        "source": {"document": document, "section": str(card.get("section", "")), "quote": card.get("quote", "")},
    }
    if rule["kind"] == "field":
        rule["constraint"] = {"field": card.get("field"), "op": card.get("op"), "value": card.get("value")}
    try:
        return Rule.model_validate(rule)
    except Exception:
        report.dropped_invalid.append(str(card.get("title", rid)))
        return None


class PolicyCompiler:
    def __init__(self, llm: LLMClient, max_tokens: int = 6000):
        self.llm = llm
        self.max_tokens = max_tokens

    def compile_document(self, title: str, text: str) -> list[dict]:
        out = self.llm.complete_json(
            [system(COMPILER_SYSTEM), user(f"DOCUMENT: {title}\n\n{text}")],
            CARDS_SCHEMA, max_tokens=self.max_tokens, tag="policy_compiler")
        return [c for c in out.get("cards", []) if isinstance(c, dict)]

    def compile(self, company: str, policy_dir: str | Path, description: str = "") -> tuple[PolicyPack, CompileReport]:
        report = CompileReport()
        rules: list[Rule] = []
        docs = sorted(Path(policy_dir).glob("*.md"))
        report.documents = len(docs)

        def one(path: Path):
            text = path.read_text()
            title = _title(path, text)
            try:
                return path, title, text, self.compile_document(title, text)
            except PendingBatch:
                return path, title, text, None

        for path, title, text, cards in self.llm.map(one, docs):
            if cards is None:
                report.pending.append(path.name)
                continue
            for c in cards:
                if not quote_found(str(c.get("quote", "")), text):
                    report.dropped_quote.append(str(c.get("title", "?")))
                    continue
                r = _card_to_rule(c, f"C-{len(rules) + 1:02d}", title, report)
                if r is not None:
                    rules.append(r)
        report.cards = len(rules)
        pack = PolicyPack.model_validate({"company": company, "description": description, "version": "compiled-1",
                                          "rules": [r.model_dump(mode="json") for r in rules]})
        return pack, report


def save_compiled(pack: PolicyPack, report: CompileReport, path: str | Path, compiler: str) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    header = (f"# Requirement cards for {pack.company}, compiled by {compiler} from the prose policies\n"
              f"# (policy/compiler.py). {report.cards} cards from {report.documents} documents; "
              f"{len(report.dropped_quote)} dropped for a quote not in the policy.\n")
    body = yaml.safe_dump(pack.model_dump(mode="json", exclude_none=True), sort_keys=False, width=110)
    Path(path).write_text(header + body)
