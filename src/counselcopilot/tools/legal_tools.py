"""Tools over the knowledge layer (design §3 Tools). Read-only except request_approval
(records a pending request a human answers) and send_to_counterparty (gated, mock)."""

from __future__ import annotations

from typing import Callable

from ..policy.schema import LawPack, PolicyPack
from .registry import Tool, ToolRegistry
from .web_search import web_search


def build_registry(pack: PolicyPack, law_pack: LawPack | None = None,
                   precedents: list[dict] | None = None, error_rate: float = 0.0, seed: int = 0,
                   search: Callable[..., dict] = web_search) -> ToolRegistry:
    reg = ToolRegistry(error_rate=error_rate, seed=seed)
    precedents = precedents or []
    pending: list[dict] = []
    sent: list[dict] = []

    def rule_lookup(rule_id: str) -> dict:
        r = pack.rule(rule_id)
        return {"id": r.id, "title": r.title, "requirement": r.requirement, "applies_if": r.applies_if,
                "approval": r.approval, "refs": r.refs}

    def statute_lookup(provision_id: str) -> dict:
        if law_pack is None:
            raise KeyError("no law pack loaded")
        p = next(x for x in law_pack.provisions if x.id == provision_id)
        return {"id": p.id, "act": p.act, "section": p.section, "summary": p.summary, "risk_level": p.risk_level}

    def approval_matrix_query(rule_id: str) -> dict:
        r = pack.rule(rule_id)
        return {"rule_id": rule_id, "deviation_allowed": r.approval is not None, "approver": r.approval}

    def precedent_search(rule_id: str, counterparty: str) -> list[dict]:
        return [p for p in precedents if p["rule_id"] == rule_id and p["counterparty"].lower() == counterparty.lower()]

    def request_approval(rule_id: str, reason: str) -> dict:
        pending.append({"rule_id": rule_id, "reason": reason})
        return {"status": "pending", "message": "Sent to senior counsel; no action until they approve."}

    def send_to_counterparty(approval_id: str, message: str) -> dict:
        sent.append({"approval_id": approval_id, "message": message})
        return {"status": "sent (mock)"}

    s = lambda **p: {"type": "object", "properties": p, "required": list(p), "additionalProperties": False}
    reg.register(Tool("rule_lookup", "Full text of a company policy rule by id.", s(rule_id={"type": "string"}), rule_lookup))
    reg.register(Tool("statute_lookup", "Summary of a US law provision by id.",
                      s(provision_id={"type": "string"}), statute_lookup))
    reg.register(Tool("web_search", "Live search of the US Code, current federal regulations and the Federal "
                      "Register. Search for a legal topic, never for NDA text. Results are unreviewed leads, not "
                      "the law pack; California law is not covered.",
                      s(query={"type": "string"}), lambda query: search(query, limit=2)))
    reg.register(Tool("approval_matrix_query", "Who may approve a deviation from a rule.",
                      s(rule_id={"type": "string"}), approval_matrix_query))
    reg.register(Tool("precedent_search", "Deviations senior counsel already approved for this counterparty.",
                      s(rule_id={"type": "string"}, counterparty={"type": "string"}), precedent_search))
    reg.register(Tool("request_approval", "Ask senior counsel to approve a deviation. Does not approve it.",
                      s(rule_id={"type": "string"}, reason={"type": "string"}), request_approval, read_only=False))
    reg.register(Tool("send_to_counterparty", "Send the draft to the other side. Needs a granted approval id.",
                      s(approval_id={"type": "string"}, message={"type": "string"}), send_to_counterparty,
                      gated=True, read_only=False))
    reg.pending, reg.sent = pending, sent  # type: ignore[attr-defined]
    return reg


# Gold minimal tool sets per finding type (design §8.3)
GOLD_TOOL_SETS = {
    "approval_needed": {"rule_lookup", "approval_matrix_query", "precedent_search", "request_approval"},
    "approval_needed_with_precedent": {"rule_lookup", "approval_matrix_query", "precedent_search"},
    "statutory_risk": {"statute_lookup"},
}
