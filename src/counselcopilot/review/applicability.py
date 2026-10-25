"""Model-judged applicability for requirement cards (design §20, chosen 25 Oct 2026).

A compiled card says when it applies in the policy's own words ("vendor NDAs where personal data
is shared"). Instead of evaluating a structured expression, the model reads those conditions
next to the deal form and the NDA segments about the parties, the purpose and the information
shared, and answers yes, no or unknown for each card. Unknown is never read as no: the card is
checked and reported as undecided, the same as an unknown fact under the structured filter.
"""

from __future__ import annotations

from ..data.draft import Draft
from ..llm import LLMClient, PendingBatch, system, user
from ..policy.schema import DealContext, Rule
from ..retrieval.index import HybridIndex

QUERIES = (
    "between party parties disclosing receiving company corporation individual employee consultant",
    "purpose evaluate discuss potential business relationship transaction services supply",
    "personal data personally identifiable information customer employee patient records privacy",
)

APPLY_SCHEMA = {
    "type": "object",
    "properties": {"answers": {"type": "array", "items": {
        "type": "object",
        "properties": {"id": {"type": "string"}, "applies": {"type": "string", "enum": ["yes", "no", "unknown"]},
                       "rationale": {"type": "string"}},
        "required": ["id", "applies", "rationale"]}}},
    "required": ["answers"],
}

APPLY_SYSTEM = """You decide which company policy requirements apply to one NDA (non-disclosure agreement).

You get the deal form the consultant filled in (blank facts are unknown), numbered SEGMENTS from the NDA, and a list of requirements, each with the condition under which it applies. For each requirement answer:
- "yes": the condition holds for this deal and NDA;
- "no": it clearly does not hold;
- "unknown": the form and the segments don't say enough to tell.

Judge only the condition, not whether the NDA complies. Use the form first; use the segments for facts the form leaves blank. Give a one-sentence rationale per requirement.

Reply with JSON {"answers": [{"id": ..., "applies": "yes"|"no"|"unknown", "rationale": ...}, ...]}."""


def form_text(deal: DealContext) -> str:
    d = deal.model_dump(mode="json")
    lines = [f"- {k}: {'(blank)' if v is None or v == 'unknown' else v}" for k, v in d.items()]
    return "\n".join(lines)


def context_segments(index: HybridIndex, k: int = 6) -> list[int]:
    ids: set[int] = set()
    for q in QUERIES:
        ids.update(int(h.passage.id) for h in index.search(q, k=k))
    return sorted(ids)


def judge_applicability(llm: LLMClient, rules: list[Rule], deal: DealContext, draft: Draft,
                        index: HybridIndex, batch: int = 15) -> tuple[dict[str, bool | None], dict[str, str]]:
    """{rule id: True / False / None} and {rule id: rationale} for rules with `applies_when`."""
    rules = [r for r in rules if r.applies_when]
    if not rules:
        return {}, {}
    ids = context_segments(index)
    out: dict[str, bool | None] = {r.id: None for r in rules}
    why: dict[str, str] = {}

    def ask(chunk: list[Rule]):
        listing = "\n".join(f"- {r.id}: {r.title}. Applies to: {r.applies_when}" for r in chunk)
        try:
            return llm.complete_json(
                [system(APPLY_SYSTEM),
                 user(f"DEAL FORM:\n{form_text(deal)}\n\nSEGMENTS:\n{draft.numbered(ids) if ids else '(none)'}"
                      f"\n\nREQUIREMENTS:\n{listing}")],
                APPLY_SCHEMA, max_tokens=120 * len(chunk) + 100, tag="applicability")
        except PendingBatch:
            raise
        except Exception:  # unreadable reply: these cards stay undecided and are checked
            return {}

    chunks = [rules[i:i + batch] for i in range(0, len(rules), batch)]
    for reply in llm.map(ask, chunks):
        for a in reply.get("answers", []) if isinstance(reply, dict) else []:
            rid = str(a.get("id", "")).strip()
            if rid in out:
                out[rid] = {"yes": True, "no": False}.get(str(a.get("applies", "")).lower())
                why[rid] = str(a.get("rationale", ""))
    return out, why
