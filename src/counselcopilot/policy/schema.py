"""Policy rule base, law pack and deal context.

A *policy pack* is one company's NDA rules after compilation (design §3.1, R2). Each rule has
an applicability condition over the deal context, so the reverse path of two-way retrieval can
select only the rules that apply to this deal before checking coverage.

Rules come in three kinds:
- require: the NDA must contain the term (missing = omission, contradicted = violation)
- forbid:  the NDA must not contain the term (present = violation)
- field:   a value in the NDA must satisfy a constraint (e.g. confidentiality term >= 36 months)

A rule may be *anchored* to a ContractNLI hypothesis (design §7.1). Anchored rules get their
ground truth on real NDAs from ContractNLI's expert labels.
"""

from __future__ import annotations

import ast
import itertools
from enum import Enum
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, Field, field_validator, model_validator

from .jurisdictions import is_us


class CounterpartyType(str, Enum):
    VENDOR = "vendor"
    CUSTOMER = "customer"
    EMPLOYEE = "employee"
    PARTNER = "partner"


class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


# Deal facts that may be left blank on the form and are then read from the NDA itself by
# the reviewer (review/deal_facts.py). Leaving them blank turns applicability into a
# reasoning step that can be scored, instead of a lookup (review problem 4).
INFERABLE_FACTS = ("personal_data", "governing_law")


class DealContext(BaseModel):
    """The short form the consultant fills in with the draft (design §2)."""

    company: str  # a US company in PolicyNDA
    counterparty_type: CounterpartyType
    personal_data: bool | None = False  # None = not on the form, infer from the NDA
    counterparty_country: str = "US"
    value_band: Literal["low", "medium", "high"] = "medium"
    # Which side the company is on; "loophole" is defined from the company's side (§7.2).
    company_side: Literal["disclosing", "receiving", "mutual"] = "disclosing"
    # Governing law as written in the NDA: lower-case US state ("delaware", "california"),
    # "united states", a lower-case country, or "unknown" (see policy/jurisdictions.py).
    # State statutes only apply under that state's law. None = infer from the NDA.
    governing_law: str | None = None

    def unknown_facts(self) -> list[str]:
        return [f for f in INFERABLE_FACTS if getattr(self, f) is None]

    def variables(self) -> dict[str, Any]:
        d = self.model_dump()
        d["counterparty"] = self.counterparty_type.value  # short alias for conditions
        d["counterparty_type"] = self.counterparty_type.value
        d["foreign"] = self.counterparty_country.strip().upper() not in ("US", "USA", "U.S.", "UNITED STATES",
                                                                          "UNITED STATES OF AMERICA")
        d["us_law"] = is_us(self.governing_law)
        return d


# ---------------------------------------------------------------- applicability conditions

_ALLOWED_NODES = (
    ast.Expression, ast.BoolOp, ast.And, ast.Or, ast.UnaryOp, ast.Not, ast.Compare,
    ast.Eq, ast.NotEq, ast.In, ast.NotIn, ast.Name, ast.Load, ast.Constant, ast.List, ast.Tuple,
)


class ConditionError(ValueError):
    pass


def compile_condition(expr: str) -> ast.Expression:
    """Parse a condition such as ``counterparty == 'vendor' and personal_data``.

    Only boolean logic, ==, !=, in, not in, names and literals are allowed; nothing is executed.
    """
    try:
        tree = ast.parse(expr.strip() or "True", mode="eval")
    except SyntaxError as e:
        raise ConditionError(f"bad condition {expr!r}: {e}") from e
    for node in ast.walk(tree):
        if not isinstance(node, _ALLOWED_NODES):
            raise ConditionError(f"{type(node).__name__} not allowed in condition {expr!r}")
    return tree


def _eval(node: ast.AST, env: dict[str, Any]) -> Any:
    if isinstance(node, ast.Expression):
        return _eval(node.body, env)
    if isinstance(node, ast.BoolOp):
        vals = (_eval(v, env) for v in node.values)
        return all(vals) if isinstance(node.op, ast.And) else any(vals)
    if isinstance(node, ast.UnaryOp):
        return not _eval(node.operand, env)
    if isinstance(node, ast.Compare):
        left = _eval(node.left, env)
        for op, comp in zip(node.ops, node.comparators):
            right = _eval(comp, env)
            ok = {
                ast.Eq: lambda a, b: a == b,
                ast.NotEq: lambda a, b: a != b,
                ast.In: lambda a, b: a in b,
                ast.NotIn: lambda a, b: a not in b,
            }[type(op)](left, right)
            if not ok:
                return False
            left = right
        return True
    if isinstance(node, ast.Name):
        if node.id in ("True", "False"):
            return node.id == "True"
        if node.id not in env:
            raise ConditionError(f"unknown deal variable {node.id!r}")
        return env[node.id]
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, (ast.List, ast.Tuple)):
        return [_eval(e, env) for e in node.elts]
    raise ConditionError(f"unsupported node {type(node).__name__}")


def evaluate_condition(expr: str, deal: DealContext) -> bool:
    return bool(_eval(compile_condition(expr), deal.variables()))


def _choices(rule: Rule, fact: str) -> tuple:
    if fact == "personal_data":
        return (True, False)
    lits = {n.value.lower() for n in ast.walk(compile_condition(rule.applies_if))
            if isinstance(n, ast.Constant) and isinstance(n.value, str)}
    us = next(s for s in ("delaware", "texas", "ohio", "utah") if s not in lits)
    return tuple(sorted(lits | {us, "united kingdom"}))


def applicability(rule: Rule, deal: DealContext) -> bool | None:
    """True / False, or None when an unknown fact decides it. Every value the rule's condition
    mentions is tried, plus one other US state and one foreign law. Gold uses it to leave such
    rules unscored; the reviewer uses it to check them anyway rather than drop them."""
    unknown = deal.unknown_facts()
    if not unknown:
        return rule.applies_to(deal)
    outcomes = {rule.applies_to(deal.model_copy(update=dict(zip(unknown, combo))))
                for combo in itertools.product(*(_choices(rule, f) for f in unknown))}
    return outcomes.pop() if len(outcomes) == 1 else None


# ---------------------------------------------------------------- rules

class SourceRef(BaseModel):
    document: str
    section: str = ""
    quote: str = ""


class Anchor(BaseModel):
    """Links a rule to a ContractNLI hypothesis for ground truth (design §7.1)."""

    hypothesis: str  # e.g. "nda-16"


# What a field is worth when the NDA has no such clause: no restriction lasts 0 months, no
# deadline never ends, no non-compete is False (gold-deals audit, point 1). Laws and forums have
# no such value: only a "not in" / "!=" rule is met by their absence.
ABSENT_VALUE = {"confidentiality_term_months": 0.0, "survival_months": 0.0, "non_solicit_months": 0.0,
                "return_deadline_days": float("inf"), "non_compete": False}


class FieldConstraint(BaseModel):
    """For field rules. Field names match the obligation-frame / NDA-field extractor."""

    field: Literal[
        "confidentiality_term_months", "governing_law", "dispute_forum", "survival_months",
        "return_deadline_days", "non_solicit_months", "non_compete",
    ]
    op: Literal[">=", "<=", "==", "!=", "in", "not in"]
    value: Any

    def check_absent(self) -> bool:
        """Is the rule met by an NDA without this clause? "Non-solicit at most 12 months" is; "term at
        least 24 months" and "return within 30 days" are not (those are omissions)."""
        if self.field in ABSENT_VALUE:
            return self.check(ABSENT_VALUE[self.field])
        return self.op in ("!=", "not in")

    def check(self, actual: Any) -> bool:
        if actual is None:
            return False
        return {
            ">=": lambda a, b: a >= b,
            "<=": lambda a, b: a <= b,
            "==": lambda a, b: a == b,
            "!=": lambda a, b: a != b,
            "in": lambda a, b: a in b,
            "not in": lambda a, b: a not in b,
        }[self.op](actual, self.value)


class Rule(BaseModel):
    id: str = Field(pattern=r"^[A-Z]+(-[A-Za-z0-9]+)+$")  # "P-07", "LAW-CA-BPC-16600"
    title: str
    requirement: str  # the rule in one plain sentence; this is what gets checked
    kind: Literal["require", "forbid", "field"]
    # The NDA term the rule is about, written as a statement about the NDA ("The Receiving
    # Party must return or destroy Confidential Information when the agreement ends.").
    # This is what the checker tests for presence. Falls back to `requirement`.
    term: str = ""
    applies_if: str = "True"
    # When the rule applies, in the policy's own words ("vendor deals that share personal data").
    # Compiled requirement cards carry it, and the reviewer's model judges it against the deal and
    # the NDA (review/applicability.py). `applies_if` is the structured version, kept as an ablation.
    applies_when: str = ""
    severity: Severity = Severity.MEDIUM
    anchor: Anchor | None = None
    constraint: FieldConstraint | None = None
    approval: str | None = None  # who may approve a deviation, e.g. "General Counsel"
    refs: list[str] = Field(default_factory=list)  # cross-reference graph edges (R6)
    source: SourceRef | None = None
    keywords: list[str] = Field(default_factory=list)  # optional retrieval hints

    @field_validator("applies_if")
    @classmethod
    def _valid_condition(cls, v: str) -> str:
        compile_condition(v)
        return v

    @model_validator(mode="after")
    def _kind_fields(self) -> "Rule":
        if self.kind == "field" and self.constraint is None:
            raise ValueError(f"{self.id}: field rules need a constraint")
        return self

    @property
    def check_term(self) -> str:
        return self.term or self.requirement

    def applies_to(self, deal: DealContext) -> bool:
        return evaluate_condition(self.applies_if, deal)

    def as_text(self) -> str:
        """Text used for indexing and prompting."""
        parts = [f"[{self.id}] {self.title}: {self.requirement}"]
        if self.approval:
            parts.append(f"Deviation requires approval by {self.approval}.")
        if self.source and self.source.quote:
            parts.append(f'Policy text: "{self.source.quote}"')
        return " ".join(parts)


class PolicyPack(BaseModel):
    company: str
    description: str = ""
    version: str = "0"
    rules: list[Rule]

    @model_validator(mode="after")
    def _unique_ids(self) -> "PolicyPack":
        ids = [r.id for r in self.rules]
        dup = {i for i in ids if ids.count(i) > 1}
        if dup:
            raise ValueError(f"duplicate rule ids: {sorted(dup)}")
        known = set(ids)
        for r in self.rules:
            for ref in r.refs:
                if ref not in known and not ref.startswith("LAW-"):
                    raise ValueError(f"{r.id} refers to unknown rule {ref}")
        return self

    def rule(self, rule_id: str) -> Rule:
        for r in self.rules:
            if r.id == rule_id:
                return r
        raise KeyError(rule_id)

    def applicable(self, deal: DealContext) -> list[Rule]:
        return [r for r in self.rules if r.applies_to(deal)]

    @classmethod
    def load(cls, path: str | Path) -> "PolicyPack":
        return cls.model_validate(yaml.safe_load(Path(path).read_text(encoding="utf-8")))


class LawProvision(BaseModel):
    """One entry of the curated US law pack. Findings are worded as risk, never as advice."""

    id: str = Field(pattern=r"^LAW-[A-Z0-9-]+$")  # e.g. "LAW-DTSA-1833B"
    act: str
    section: str
    title: str
    summary: str  # plain-language summary, checked by two teammates
    risk_pattern: str  # forbid: what in an NDA triggers the risk; require: the term that must be there
    kind: Literal["forbid", "require"] = "forbid"
    applies_if: str = "True"
    # Which governing law makes the provision bite: [] = always (federal law, or privacy law
    # that follows the data), ["us"] = any US state, ["california"] = California only.
    requires_law: list[str] = Field(default_factory=list)
    # "risk" for clear-cut provisions; "possible_risk" where courts are split or thresholds
    # apply (e.g. employee non-solicits in California). Findings are worded with this.
    risk_level: Literal["risk", "possible_risk"] = "risk"
    severity: Severity = Severity.HIGH
    source_url: str = ""
    checked_by: list[str] = Field(default_factory=list)  # two teammates before use

    @field_validator("applies_if")
    @classmethod
    def _valid_condition(cls, v: str) -> str:
        compile_condition(v)
        return v

    def _condition(self) -> str:
        if not self.requires_law:
            return self.applies_if
        law = " or ".join("us_law" if j == "us" else f"governing_law == {j!r}" for j in self.requires_law)
        return f"({law}) and ({self.applies_if})"

    def as_rule(self) -> Rule:
        """Law provisions are checked like 'forbid' rules (the risky pattern must be absent)."""
        return Rule(
            id=self.id,
            title=f"{self.act} {self.section}: {self.title}",
            requirement=(f"The NDA must not contain: {self.risk_pattern}" if self.kind == "forbid"
                         else f"The NDA must contain: {self.risk_pattern}"),
            term=self.risk_pattern,
            kind=self.kind,
            applies_if=self._condition(),
            severity=self.severity,
            source=SourceRef(document=self.act, section=self.section, quote=self.summary),
        )


class LawPack(BaseModel):
    jurisdiction: str = "United States"
    version: str
    as_of: str  # date the law pack was checked
    provisions: list[LawProvision]

    def as_rules(self) -> list[Rule]:
        return [p.as_rule() for p in self.provisions]

    def unchecked(self) -> list[str]:
        return [p.id for p in self.provisions if len(p.checked_by) < 2]

    @classmethod
    def load(cls, path: str | Path) -> "LawPack":
        return cls.model_validate(yaml.safe_load(Path(path).read_text(encoding="utf-8")))
