"""Red-team and repair loop (RQ2, design §5) and its baselines R1, R1+A and R2.

    findings ──► opposing counsel (escape scenarios, verified against the draft text)
        ▲              │
        │              ▼
        │        repairer (smallest redline per open problem)
        │              │
        │              ▼
        └──── regression checker (re-run every applicable rule, the law pack and the consistency
              tools on the edited draft; diff: fixed / still open / NEW)

Stopping rule: stop when the attacker finds no new verified scenario and the checker finds no
open or new problem ("clean"); escalate to senior counsel when the round or token budget runs out,
when the repairer cannot fix what is left, or when two rules cannot both be met (a min/max pair
that excludes every value, or a rule that comes back after it was fixed: an oscillation).

Baselines, all from the same findings and under the same token budget (checker tokens included):
- R1   one-shot "fix all these issues";
- R1+A one-shot repair given the attacker's verified scenarios (is the gain the loop, or just the
       attacker's extra information?);
- R2   Self-Refine: repair, self-critique, repair again; no attacker and no full re-check.
Ablations: no attacker, no regression check, 1 vs 3 rounds, attacker on a different model.

Final RQ2 scores never use the loop's own checker (eval/evaluator.py, experiments/rq2.py).
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable

from ..data.draft import Draft, Edit
from ..llm import LLMClient
from ..policy.schema import DealContext, Rule
from ..review.findings import Finding
from .attacker import OpposingCounsel, Scenario
from .repairer import Problem, Repairer, edit_size, problems_from_findings, problems_from_scenarios

Detector = Callable[[Draft, DealContext], list[Finding]]


@dataclass
class RoundLog:
    round: int
    base: Draft  # the draft the edits index into
    edits: list[Edit]
    dropped: list[str] = field(default_factory=list)
    scenarios: list[Scenario] = field(default_factory=list)
    fixed: list[str] = field(default_factory=list)  # finding keys "rule:type"
    still_open: list[str] = field(default_factory=list)
    new: list[str] = field(default_factory=list)
    tokens: int = 0


@dataclass
class RepairResult:
    system: str
    original: Draft
    final: Draft
    rounds: list[RoundLog] = field(default_factory=list)
    stopped: str = "clean"  # clean | max_rounds | budget | stuck | conflict | no_problems
    escalations: list[dict] = field(default_factory=list)
    scenarios: list[Scenario] = field(default_factory=list)
    tokens: int = 0

    @property
    def edits(self) -> list[Edit]:
        return [e for r in self.rounds for e in r.edits]

    def summary(self) -> dict:
        size = [edit_size(r.base, r.edits) for r in self.rounds]
        return {"system": self.system, "rounds": len(self.rounds), "stopped": self.stopped,
                "n_edits": len(self.edits), "edit_segments": sum(s["segments"] for s in size),
                "edit_words": sum(s["words"] for s in size), "n_escalations": len(self.escalations),
                "n_scenarios": sum(bool(s.verified) for s in self.scenarios), "tokens": self.tokens,
                "new_problems_seen": sum(len(r.new) for r in self.rounds)}


def tokens_used(clients: list[LLMClient]) -> int:
    seen, total = set(), 0
    for c in clients:
        if id(c) in seen:
            continue
        seen.add(id(c))
        u = c.total_usage()
        total += u.input_tokens + u.output_tokens + u.cached_input_tokens + u.cached_output_tokens
    return total


def _key(f: Finding) -> str:
    return f"{f.rule_id}:{f.type.value}"


def field_conflicts(rules: list[Rule], deal: DealContext) -> list[dict]:
    """Applicable min/max field rules that no value can meet together (e.g. term >= 60 and <= 36)."""
    lo: dict[str, list[Rule]] = defaultdict(list)
    hi: dict[str, list[Rule]] = defaultdict(list)
    for r in rules:
        if r.kind != "field" or r.constraint is None or not isinstance(r.constraint.value, (int, float)):
            continue
        try:
            if not r.applies_to(deal):
                continue
        except Exception:
            continue
        if r.constraint.op == ">=":
            lo[r.constraint.field].append(r)
        elif r.constraint.op == "<=":
            hi[r.constraint.field].append(r)
    out = []
    for f in set(lo) & set(hi):
        a = max(lo[f], key=lambda r: r.constraint.value)
        b = min(hi[f], key=lambda r: r.constraint.value)
        if a.constraint.value > b.constraint.value:
            out.append({"reason": "conflict", "field": f, "rules": [a.id, b.id],
                        "note": f"{a.id} needs >= {a.constraint.value} but {b.id} allows <= {b.constraint.value}"})
    return out


class RedTeamRepairLoop:
    def __init__(self, repairer: Repairer, detector: Detector | None, attacker: OpposingCounsel | None,
                 rules: list[Rule], max_rounds: int = 3, token_budget: int | None = None,
                 clients: list[LLMClient] | None = None, name: str = "loop"):
        self.repairer, self.detector, self.attacker = repairer, detector, attacker
        self.rules = {r.id: r for r in rules}
        self.max_rounds, self.budget = max_rounds, token_budget
        self.clients = clients or [repairer.llm]
        self.name = name

    def run(self, draft: Draft, deal: DealContext, findings: list[Finding]) -> RepairResult:
        t0 = tokens_used(self.clients)
        res = RepairResult(self.name, draft, draft)
        conflicts = field_conflicts(list(self.rules.values()), deal)
        blocked = {rid for c in conflicts for rid in c["rules"]}
        res.escalations += conflicts
        open_f = [f for f in findings if f.rule_id not in blocked]
        known: list[Scenario] = []
        fixed_once: set[str] = set()
        current = draft
        first_keys = {_key(f) for f in findings}
        for rnd in range(1, self.max_rounds + 1):
            if self.budget and tokens_used(self.clients) - t0 >= self.budget:
                res.stopped = "budget"
                break
            new_s = self.attacker.attack(current, deal, open_f, known, rnd) if self.attacker else []
            res.scenarios += new_s
            known += [s for s in new_s if s.verified]
            open_s = [s for s in known if any(t in current.segments for t in s.texts)]
            if not open_f and not open_s:  # nothing open and the attacker found nothing new
                res.stopped = "clean"
                break
            problems = problems_from_findings(open_f, self.rules) + problems_from_scenarios(open_s)
            edits, dropped = self.repairer.repair(current, problems)
            log = RoundLog(rnd, current, edits, dropped, new_s)
            if not edits:
                res.rounds.append(log)
                res.stopped = "stuck"
                res.escalations += [{"reason": "stuck", "problem": p.id} for p in problems]
                break
            after = current.apply(edits)
            if self.detector is not None:
                found = self.detector(after, deal)
                before = {_key(f) for f in open_f}
                now = {_key(f): f for f in found if f.rule_id not in blocked}
                log.fixed = sorted(before - set(now))
                log.still_open = sorted(before & set(now))
                log.new = sorted(set(now) - before - (first_keys - before))
                back = [k for k in now if k in fixed_once]
                for k in back:  # fixed earlier, broken again: two rules pull the clause in opposite ways
                    res.escalations.append({"reason": "conflict", "problem": k, "note": "fixed, then broken again"})
                    blocked.add(k.split(":")[0])
                fixed_once |= set(log.fixed)
                open_f = [f for k, f in now.items() if k not in back]
                if not log.fixed and not log.new and not new_s:
                    # no progress: the same problems are open after the repair; another round would
                    # only repeat it, so hand what is left to senior counsel
                    log.tokens = tokens_used(self.clients) - t0
                    res.rounds.append(log)
                    current = after
                    res.stopped = "stuck"
                    res.escalations += [{"reason": "stuck", "problem": _key(f)} for f in open_f]
                    break
            else:  # no regression check: trust the repairer
                log.fixed = sorted(_key(f) for f in open_f)
                open_f = []
            log.tokens = tokens_used(self.clients) - t0
            res.rounds.append(log)
            current = after
        else:
            res.stopped = "max_rounds"
        if res.stopped in ("max_rounds", "budget") and open_f:
            res.escalations += [{"reason": res.stopped, "problem": _key(f)} for f in open_f]
        if any(e["reason"] == "conflict" for e in res.escalations) and res.stopped == "clean":
            res.stopped = "conflict"
        res.final = current
        res.tokens = tokens_used(self.clients) - t0
        return res


def one_shot(repairer: Repairer, draft: Draft, findings: list[Finding], rules: list[Rule],
             attacker: OpposingCounsel | None = None, deal: DealContext | None = None,
             clients: list[LLMClient] | None = None) -> RepairResult:
    """R1 (no attacker) and R1+A (one attacker call, its verified scenarios added as problems)."""
    clients = clients or [repairer.llm]
    t0 = tokens_used(clients)
    rmap = {r.id: r for r in rules}
    scen = attacker.attack(draft, deal, findings, [], 1) if attacker is not None and deal is not None else []
    problems = problems_from_findings(findings, rmap) + problems_from_scenarios(scen)
    res = RepairResult("r1_attacker" if attacker else "r1", draft, draft, scenarios=scen)
    if not problems:
        res.stopped = "no_problems"
        return res
    edits, dropped = repairer.repair(draft, problems, one_shot=True, tag="one_shot_repair")
    res.rounds.append(RoundLog(1, draft, edits, dropped, scen, tokens=tokens_used(clients) - t0))
    res.final = draft.apply(edits)
    res.stopped = "clean" if edits else "stuck"
    res.tokens = tokens_used(clients) - t0
    return res


def self_refine(repairer: Repairer, draft: Draft, findings: list[Finding], rules: list[Rule],
                max_rounds: int = 3, token_budget: int | None = None,
                clients: list[LLMClient] | None = None) -> RepairResult:
    """R2: repair -> self-critique -> repair, no attacker and no full re-check."""
    clients = clients or [repairer.llm]
    t0 = tokens_used(clients)
    rmap = {r.id: r for r in rules}
    res = RepairResult("r2_self_refine", draft, draft)
    problems: list[Problem] = problems_from_findings(findings, rmap)
    original = list(problems)
    current = draft
    for rnd in range(1, max_rounds + 1):
        if not problems:
            res.stopped = "clean"
            break
        if token_budget and tokens_used(clients) - t0 >= token_budget:
            res.stopped = "budget"
            break
        edits, dropped = repairer.repair(current, problems, one_shot=rnd == 1, tag="self_refine_repair")
        res.rounds.append(RoundLog(rnd, current, edits, dropped, tokens=tokens_used(clients) - t0))
        current = current.apply(edits)
        remaining, done = repairer.critique(current, original)
        if done or not remaining:
            res.stopped = "clean"
            break
        problems = remaining
    else:
        res.stopped = "max_rounds"
    res.final = current
    res.tokens = tokens_used(clients) - t0
    return res
