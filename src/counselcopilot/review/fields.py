"""Field extraction for field rules (governing law, term length, ...).

This is a prompted stand-in. The design replaces it with obligation frames from the QLoRA
model (design §6, R4); the interface (field name -> value + evidence) stays the same.
"""

from __future__ import annotations

import re

from ..data.draft import Draft
from ..llm import LLMClient, PendingBatch, system, user
from ..policy.jurisdictions import normalise_jurisdiction
from ..policy.schema import FieldConstraint, Rule
from ..retrieval.index import HybridIndex
from .checker import CheckResult
from .findings import Finding, FindingType

FIELD_QUESTIONS = {
    "confidentiality_term_months": "How long do the confidentiality obligations last, in months? "
    "Answer a number of months. If they last indefinitely or perpetually, answer 9999. "
    "If the NDA does not say, answer null.",
    "survival_months": "For how many months do obligations survive termination? Number of months, or null.",
    "return_deadline_days": "Within how many days must confidential information be returned or destroyed? "
    "Number of days, or null.",
    "non_solicit_months": "How many months does any non-solicitation obligation last? Number, or null if none.",
    "governing_law": "Which law governs the agreement? If it is a US state, answer the state in lower case "
    "(e.g. 'delaware', 'new york'); otherwise the country in lower case (e.g. 'england', 'singapore'); "
    "null if the NDA does not say.",
    "dispute_forum": "Where are disputes resolved (courts or arbitration seat)? US state in lower case if in "
    "the US, otherwise the country in lower case, or null.",
    "non_compete": "Does the NDA restrict a party from carrying on a business or competing? true or false.",
}

FIELD_QUERIES = {
    "confidentiality_term_months": "term period years months confidentiality obligations expire duration",
    "survival_months": "survive termination expiration years",
    "return_deadline_days": "return destroy confidential information days request termination",
    "non_solicit_months": "solicit hire employees months",
    "governing_law": "governed construed laws of",
    "dispute_forum": "jurisdiction courts arbitration seat venue disputes",
    "non_compete": "compete competing business restrict engage",
}

BLANK = "blank"
TEMPLATE_NOTE = (" If the NDA is a template and leaves this value blank (for example '____ years' or "
                 "'[number]'), answer \"blank\".")

FIELD_SCHEMA = {
    "type": "object",
    "properties": {
        "value": {"type": ["string", "number", "boolean", "null"]},
        "evidence": {"type": "array", "items": {"type": "integer"}},
    },
    "required": ["value", "evidence"],
    "additionalProperties": False,
}


_WORDS = {w: i for i, w in enumerate(
    "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen "
    "seventeen eighteen nineteen twenty".split())}
_WORDS.update({"thirty": 30, "forty": 40, "forty-five": 45, "fifty": 50, "sixty": 60, "ninety": 90, "a": 1, "an": 1})
_PER = {"months": {"year": 12, "month": 1, "week": 12 / 52, "day": 12 / 365},
        "days": {"year": 365, "month": 30, "week": 7, "day": 1}}


def _duration(text: str, unit: str) -> float | None:
    """"2 years", "two (2) years", "36" -> a number in `unit` (months or days); perpetual -> 9999.
    A bare number is taken to be in `unit` already (audit 23 Oct: "2 years" used to give 2 months)."""
    t = text.strip().lower()
    if re.search(r"perpetu|indefinite|no (?:time )?limit|unlimited", t):
        return 9999.0
    m = re.search(r"(\d+(?:\.\d+)?|\b(?:%s)\b)\s*(?:\(\d+\)\s*)?(year|month|week|day)?" % "|".join(
        sorted(_WORDS, key=len, reverse=True)), t)
    if not m:
        return None
    n = float(m.group(1)) if m.group(1)[0].isdigit() else float(_WORDS[m.group(1)])
    return round(n * _PER[unit][m.group(2)], 2) if m.group(2) else n


def _normalise(field: str, v):
    if v is None or v == "" or v == "null":
        return None
    if str(v).strip().lower() == BLANK:
        return BLANK
    if field == "non_compete":
        return v if isinstance(v, bool) else str(v).lower() in ("true", "yes")
    if field.endswith(("_months", "_days")):
        if isinstance(v, (int, float)):
            return float(v)
        return _duration(str(v), "months" if field.endswith("_months") else "days")
    if field in ("governing_law", "dispute_forum"):
        return normalise_jurisdiction(str(v))
    return str(v).strip().lower()


def extract_field(llm: LLMClient, field: str, draft: Draft, index: HybridIndex, k: int = 6):
    hits = index.search(FIELD_QUERIES[field], k=k)
    ids = sorted(int(h.passage.id) for h in hits)
    if not ids:
        return None, []
    out = llm.complete_json(
        [system("You extract facts from NDAs. Use only the numbered segments. Reply with JSON "
                '{"value": ..., "evidence": [segment numbers]}.'),
         user(f"QUESTION: {FIELD_QUESTIONS[field]}{TEMPLATE_NOTE}\n\nSEGMENTS:\n{draft.numbered(ids)}")],
        FIELD_SCHEMA, max_tokens=120, tag="field_extract")
    ev = [int(i) for i in out.get("evidence", []) if isinstance(i, (int, float)) and int(i) in ids]
    return _normalise(field, out.get("value")), ev


def check_field_rule(llm: LLMClient, rule: Rule, draft: Draft, index: HybridIndex) -> tuple[Finding | None, CheckResult]:
    c: FieldConstraint = rule.constraint  # type: ignore[assignment]
    try:
        value, ev = extract_field(llm, c.field, draft, index)
    except PendingBatch:
        raise
    except Exception as e:  # malformed reply: no finding, counted under check_errors
        return None, CheckResult("NotMentioned", [], 0.0, "", [], error=str(e)[:200])
    if value == BLANK:
        # Template with the value left blank: tell the consultant to fill it in, but it is
        # neither compliant nor an omission, so it is not a finding (review problem 2).
        return None, CheckResult("NotMentioned", ev, 0.0, f"{c.field} left blank in template")
    if value is None:
        res = CheckResult("NotMentioned", [], 0.6, f"{c.field} not found")
        ftype = FindingType.OMISSION
    elif c.check(value):
        return None, CheckResult("Entailment", ev, 0.8, f"{c.field}={value}")
    else:
        res = CheckResult("Contradiction", ev, 0.8, f"{c.field}={value}, rule needs {c.op} {c.value}")
        ftype = FindingType.APPROVAL_NEEDED if rule.approval else FindingType.VIOLATION
    return Finding(draft_id=draft.id, rule_id=rule.id, type=ftype, evidence=res.evidence,
                   explanation=res.rationale, confidence=res.confidence, reviewer="policy_reviewer",
                   direction="field", severity=rule.severity.value), res
