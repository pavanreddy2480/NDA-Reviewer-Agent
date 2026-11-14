"""One-hop cross-reference graph over the policy and law packs (design §4 T6).

A rule often points at another: a minimum term refers to the approval route for shorter terms,
a data rule refers to the security rule it relies on. Retrieving a rule without the rule it points
to loses the exception or the approver. The graph has an edge for every `refs` entry (both
directions), plus an edge from each rule to the approval rule of the same field or topic.

Used by the policy reviewer when `ReviewConfig.xref` is on:
- forward retrieval: a rule hit by a clause also brings its one-hop neighbours to that clause;
- findings: a violation of a rule with no approver of its own names the approver of a linked
  rule (`approver`), so the hand-off knows whom to ask. The finding type is not changed, because
  gold takes the type from the rule itself.
"""

from __future__ import annotations

from collections import defaultdict

from ..policy.schema import Rule


class CrossRefGraph:
    def __init__(self, rules: list[Rule]):
        self.rules = {r.id: r for r in rules}
        self.edges: dict[str, set[str]] = defaultdict(set)
        for r in rules:
            for ref in r.refs:
                if ref in self.rules:
                    self.edges[r.id].add(ref)
                    self.edges[ref].add(r.id)
        # rules about the same field share approval routes (a min-term rule and a max-term rule)
        by_field: dict[str, list[str]] = defaultdict(list)
        for r in rules:
            if r.kind == "field" and r.constraint is not None:
                by_field[r.constraint.field].append(r.id)
        for ids in by_field.values():
            for a in ids:
                for b in ids:
                    if a != b:
                        self.edges[a].add(b)

    def neighbours(self, rule_id: str) -> list[str]:
        return sorted(self.edges.get(rule_id, ()))

    def expand(self, rule_ids) -> list[str]:
        out = set(rule_ids)
        for rid in list(out):
            out.update(self.neighbours(rid))
        return sorted(out)

    def approver(self, rule_id: str) -> str | None:
        """The rule's own approver, else the approver of a one-hop neighbour."""
        r = self.rules.get(rule_id)
        if r is None:
            return None
        if r.approval:
            return r.approval
        for n in self.neighbours(rule_id):
            if self.rules[n].approval:
                return self.rules[n].approval
        return None

    def n_edges(self) -> int:
        return sum(len(v) for v in self.edges.values()) // 2
