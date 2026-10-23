"""The rule-check primitive: does the NDA contain a given term?

One call answers, for one term and a few numbered NDA segments, whether the segments
state the term (Entailment), say something incompatible (Contradiction) or don't address it
(NotMentioned). The labels deliberately match ContractNLI's, so the same primitive is
(a) the policy reviewer's check, (b) the regression checker's check in the repair loop, and
(c) the "prompted model" baseline that the QLoRA model is compared against on ContractNLI.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..data.draft import Draft
from ..llm import PendingBatch, LLMClient, system, user
from ..policy.schema import Rule
from .findings import Finding, FindingType

LABELS = ("Entailment", "Contradiction", "NotMentioned")

CHECK_SCHEMA = {
    "type": "object",
    "properties": {
        "rationale": {"type": "string"},
        "label": {"type": "string", "enum": list(LABELS)},
        "evidence": {"type": "array", "items": {"type": "integer"}},
        "confidence": {"type": "number"},
    },
    "required": ["rationale", "label", "evidence", "confidence"],
    "additionalProperties": False,
}

CHECK_SYSTEM = """You review non-disclosure agreements (NDAs). You are given a STATEMENT about a contract term and numbered SEGMENTS from one NDA.

Decide one label:
- "Entailment": the segments state the term, fully or in substance.
- "Contradiction": the segments deal with the same matter but say something incompatible with the statement.
- "NotMentioned": the segments do not address the term.

Rules:
- Use only the segments shown. Do not assume text that is not there.
- Watch for exceptions and carve-outs ("except", "unless", "provided that"); they often turn an apparent match into a contradiction.
- "evidence" lists the segment numbers that support Entailment or Contradiction. It is empty for NotMentioned.
- "confidence" is your probability (0 to 1) that the label is correct.
- Keep "rationale" to one or two sentences and write it before deciding.

Reply with a JSON object: {"rationale": ..., "label": ..., "evidence": [...], "confidence": ...}"""


def check_prompt(term: str, draft: Draft, segment_ids: list[int]) -> list:
    return [
        system(CHECK_SYSTEM),
        user(f"STATEMENT: {term}\n\nSEGMENTS:\n{draft.numbered(segment_ids)}"),
    ]


@dataclass
class CheckResult:
    label: str
    evidence: list[int]
    confidence: float
    rationale: str = ""
    shown: list[int] = field(default_factory=list)  # segments the model saw
    error: str = ""


def run_check(llm: LLMClient, term: str, draft: Draft, segment_ids: list[int],
              tag: str = "check", max_tokens: int = 300, temperature: float = 0.0,
              seed: int = 0) -> CheckResult:
    if not segment_ids:
        return CheckResult("NotMentioned", [], 1.0, "no segments retrieved", [])
    try:
        out = llm.complete_json(check_prompt(term, draft, segment_ids), CHECK_SCHEMA,
                                max_tokens=max_tokens, tag=tag, temperature=temperature, seed=seed)
        label = out.get("label", "NotMentioned")
        if label not in LABELS:
            label = "NotMentioned"
        shown = set(segment_ids)
        ev = [int(i) for i in out.get("evidence", []) if isinstance(i, (int, float)) and int(i) in shown]
        conf = out.get("confidence")
        conf = 0.5 if not isinstance(conf, (int, float)) else float(conf)
        return CheckResult(label, ev if label != "NotMentioned" else [], min(max(conf, 0.0), 1.0),
                           str(out.get("rationale", "")), list(segment_ids))
    except PendingBatch:  # queued for the Batch API: the NDA waits for the next round
        raise
    except Exception as e:  # malformed output counts as a failed check, never a crash
        return CheckResult("NotMentioned", [], 0.0, "", list(segment_ids), error=str(e)[:200])


def finding_from_check(rule: Rule, res: CheckResult, draft_id: str, *, direction: str,
                       reviewer: str = "policy_reviewer", allow_omission: bool = True) -> Finding | None:
    """Map a check label to a finding according to the rule kind.

    require: Entailment -> fine, Contradiction -> violation, NotMentioned -> omission
    forbid:  Entailment -> violation, otherwise fine
    A finding on a rule with an approval route is an approval-needed deviation rather than a
    plain violation (design §7.2).
    """
    if res.error:  # a failed check is no evidence of anything; rq1 counts it under check_errors
        return None
    ftype: FindingType | None = None
    if rule.kind == "require":
        if res.label == "Contradiction":
            ftype = FindingType.VIOLATION
        elif res.label == "NotMentioned" and allow_omission:
            ftype = FindingType.OMISSION
    elif rule.kind == "forbid" and res.label == "Entailment":
        ftype = FindingType.VIOLATION
    if ftype is None:
        return None
    if rule.id.startswith("LAW-"):
        ftype = FindingType.STATUTORY_RISK
    elif ftype == FindingType.VIOLATION and rule.approval:
        ftype = FindingType.APPROVAL_NEEDED
    return Finding(
        draft_id=draft_id, rule_id=rule.id, type=ftype, evidence=res.evidence,
        explanation=res.rationale, confidence=res.confidence, reviewer=reviewer,
        direction=direction, severity=rule.severity.value,
    )
