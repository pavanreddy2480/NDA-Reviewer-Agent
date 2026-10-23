"""Read deal facts the consultant left blank on the form from the NDA itself.

Making some facts implicit (personal data shared? which law governs?) turns applicability
into a reasoning step with its own gold labels, instead of a lookup that is right by
construction (review problems 1 and 4). Every inferred fact is logged so its accuracy can be
scored against the hand labels.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..data.draft import Draft
from ..llm import LLMClient, PendingBatch, system, user
from ..policy.schema import DealContext
from ..retrieval.index import HybridIndex
from .fields import BLANK, extract_field

PD_QUERY = "personal data personally identifiable information employee customer data privacy processing"
PD_SCHEMA = {
    "type": "object",
    "properties": {"rationale": {"type": "string"}, "personal_data": {"type": "boolean"},
                   "evidence": {"type": "array", "items": {"type": "integer"}}},
    "required": ["rationale", "personal_data", "evidence"],
    "additionalProperties": False,
}


@dataclass
class InferredFact:
    name: str
    value: object
    evidence: list[int]


def infer_personal_data(llm: LLMClient, draft: Draft, index: HybridIndex, k: int = 8) -> InferredFact:
    ids = sorted(int(h.passage.id) for h in index.search(PD_QUERY, k=k))
    if not ids:
        return InferredFact("personal_data", False, [])
    out = llm.complete_json(
        [system("You read NDAs. Decide whether information about identifiable people (personal data: "
                "employee, customer or patient records, contact details, health or financial data of "
                "individuals) is expected to be shared under this NDA. Use only the numbered segments. "
                'Reply with JSON {"rationale": ..., "personal_data": true|false, "evidence": [...]}.'),
         user(f"SEGMENTS:\n{draft.numbered(ids)}")],
        PD_SCHEMA, max_tokens=200, tag="deal_facts")
    ev = [int(i) for i in out.get("evidence", []) if isinstance(i, (int, float)) and int(i) in ids]
    return InferredFact("personal_data", bool(out.get("personal_data", False)), ev)


def resolve_deal(llm: LLMClient, deal: DealContext, draft: Draft,
                 index: HybridIndex) -> tuple[DealContext, list[InferredFact]]:
    """Fill every blank (None) inferable fact; returns the completed deal and what was inferred."""
    facts: list[InferredFact] = []
    for name in deal.unknown_facts():
        try:
            if name == "personal_data":
                facts.append(infer_personal_data(llm, draft, index))
            elif name == "governing_law":
                value, ev = extract_field(llm, "governing_law", draft, index)
                facts.append(InferredFact("governing_law", value, ev))
        except PendingBatch:
            raise
        except Exception:  # a malformed reply leaves the fact unknown instead of crashing the run
            facts.append(InferredFact(name, None, []))
    update = {f.name: f.value for f in facts}
    if "governing_law" in update and update["governing_law"] in (None, BLANK):
        update["governing_law"] = "unknown"
    return deal.model_copy(update=update), facts
