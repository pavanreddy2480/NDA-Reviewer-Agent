"""Independent evaluator for RQ2 (review problem 6; audit 22 Oct).

An edited draft has no ContractNLI labels, so "remaining defects", "regression rate" and
"repair success" all need something to check the edited text. If that were the loop's own
checker, the repairer could learn to satisfy it without fixing anything. So final RQ2 scores
use this evaluator, which:
- runs on a backend never used inside the loop or to build the benchmark (configs: evaluator);
- uses its own prompt wording, so its errors are less correlated with the loop's checker;
- checks field rules (term lengths, governing law) with the field extractor plus the exact
  constraint, so interacting min/max rules are scored deterministically;
- counts a fix or regression only if a second call (another seed) agrees, and reports the
  flip rate on unchanged drafts (`noise_floor`) so evaluator noise is not read as regressions;
- attributes regressions to individual redlines (`attribute`), for H2's per-redline rate;
- is validated for free against ContractNLI expert labels on unedited NDAs
  (`validate_on_contractnli`) and against ~100 human labels on edited drafts (`validate`),
  with Cohen's kappa and its 95% CI next to every RQ2 result.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from ..data.draft import Draft, Edit
from ..llm import LLMClient, system, user
from ..retrieval.index import HybridIndex, Passage
from ..review.fields import check_field_rule
from ..policy.schema import DealContext, Rule
from ..review.checker import CHECK_SCHEMA, CheckResult, LABELS
from .metrics import cohen_kappa

EVAL_SYSTEM = """You are auditing a revised contract for a senior lawyer. Read the whole NDA below and decide whether it contains the CONTRACT TERM.

Answer "Entailment" if the NDA contains the term (in any wording), "Contradiction" if it says something incompatible with it, and "NotMentioned" if it does not deal with it. Exceptions and carve-outs count. Cite segment numbers as evidence. Give your probability of being right as confidence, and a one-sentence rationale first.

Reply with JSON {"rationale": ..., "label": ..., "evidence": [...], "confidence": ...}."""


@dataclass
class RuleStatus:
    rule_id: str
    ok: bool  # the draft satisfies the rule
    result: CheckResult


class IndependentEvaluator:
    def __init__(self, llm: LLMClient):
        self.llm = llm

    def check(self, rule: Rule, draft: Draft, seed: int = 0) -> RuleStatus:
        if rule.kind == "field":
            index = HybridIndex([Passage(str(i), t) for i, t in enumerate(draft.segments)])
            f, res = check_field_rule(self.llm, rule, draft, index)
            return RuleStatus(rule.id, f is None and not res.error, res)
        out = self.llm.complete_json(
            [system(EVAL_SYSTEM), user(f"CONTRACT TERM: {rule.check_term}\n\nNDA:\n{draft.numbered()}")],
            CHECK_SCHEMA, max_tokens=300, tag="independent_eval", seed=seed, temperature=0.0 if seed == 0 else 0.7)
        label = out.get("label") if out.get("label") in LABELS else "NotMentioned"
        conf = out.get("confidence")
        res = CheckResult(label, [int(i) for i in out.get("evidence", []) if isinstance(i, (int, float))],
                          float(conf) if isinstance(conf, (int, float)) else 0.5, str(out.get("rationale", "")))
        ok = (label == "Entailment") if rule.kind == "require" else (label != "Entailment")
        return RuleStatus(rule.id, ok, res)

    def _confirmed(self, rule: Rule, draft: Draft, status: bool) -> bool:
        """A second call with another seed agrees with `status` (field rules are deterministic)."""
        return rule.kind == "field" or self.check(rule, draft, seed=1).ok == status

    def score_repair(self, before: Draft, after: Draft, rules: list[Rule], deal: DealContext) -> dict:
        """Status of every applicable rule (term and field) before and after repair.
        A fix (broken -> ok) or regression (ok -> broken) counts only if confirmed twice."""
        rules = [r for r in rules if r.applies_to(deal)]
        by_id = {r.id: r for r in rules}
        b = {r.id: self.check(r, before) for r in rules}
        a = {r.id: self.check(r, after) for r in rules}
        fixed = [i for i in b if not b[i].ok and a[i].ok and self._confirmed(by_id[i], after, True)]
        regressions = [i for i in b if b[i].ok and not a[i].ok and self._confirmed(by_id[i], after, False)]
        # an unconfirmed ok -> broken flip is treated as evaluator noise, not as a remaining defect
        remaining = sorted(set(i for i in a if not a[i].ok and (not b[i].ok or i in regressions)))
        return {"fixed": fixed, "remaining": remaining, "regressions": regressions, "n_rules": len(rules),
                "edit_segments_changed": changed_segments(before, after)}

    def attribute(self, before: Draft, edits: list[Edit], rules: list[Rule], regressed: list[str]) -> dict[int, list[str]]:
        """Which redline causes which regression: apply each edit alone and re-check only the
        regressed rules. H2's regression rate = share of redlines with at least one."""
        by_id = {r.id: r for r in rules}
        out: dict[int, list[str]] = {}
        for k, e in enumerate(edits):
            one = before.apply([e])
            out[k] = [rid for rid in regressed if not self.check(by_id[rid], one).ok]
        return out

    def noise_floor(self, drafts: list[Draft], rules: list[Rule], deal_of: dict[str, DealContext],
                    n: int = 20, seed: int = 0) -> dict:
        """A/A test: check unchanged drafts twice (two seeds) and report the flip rate. RQ2
        regression and fix rates are reported next to this floor."""
        rng = random.Random(seed)
        pairs = [(d, r) for d in drafts for r in rules if r.kind != "field" and r.applies_to(deal_of[d.id])]
        flips = [self.check(r, d).ok != self.check(r, d, seed=1).ok for d, r in rng.sample(pairs, min(n, len(pairs)))]
        return {"n": len(flips), "flip_rate": round(sum(flips) / max(len(flips), 1), 4)}

    def validate_on_contractnli(self, docs, hypotheses: dict[str, str], n: int = 200, seed: int = 0) -> dict:
        """Agreement with ContractNLI's expert labels on unedited test NDAs: no human time.
        Each item is (NDA, hypothesis); the evaluator answers for the hypothesis as the term."""
        rng = random.Random(seed)
        items = [(d, h) for d in docs for h in d.annotations]
        gold, pred = [], []
        for d, h in rng.sample(items, min(n, len(items))):
            rule = Rule(id="EVAL-1", title=h, requirement=hypotheses[h], term=hypotheses[h], kind="require")
            pred.append(self.check(rule, Draft.from_nda(d)).result.label)
            gold.append(d.annotations[h].label.value)
        return {"n": len(gold), "agreement": round(sum(g == p for g, p in zip(gold, pred)) / max(len(gold), 1), 4),
                "kappa": cohen_kappa(gold, pred), "kappa_ci95": kappa_ci(gold, pred)}

    @staticmethod
    def validate(human_ok: list[bool], model_ok: list[bool]) -> dict:
        agree = sum(h == m for h, m in zip(human_ok, model_ok))
        return {"n": len(human_ok), "agreement": round(agree / max(len(human_ok), 1), 4),
                "kappa": cohen_kappa(human_ok, model_ok), "kappa_ci95": kappa_ci(human_ok, model_ok)}


def changed_segments(before: Draft, after: Draft) -> int:
    """Segments the repair added, changed or removed (planted text in `before` is not counted)."""
    b, a = list(before.segments), list(after.segments)
    added = sum(1 for s in a if s not in b)
    removed = sum(1 for s in b if s not in a)
    return max(added, removed)


def kappa_ci(a: list, b: list, n: int = 2000, seed: int = 0) -> list[float]:
    if not a:
        return [0.0, 0.0]
    rng = random.Random(seed)
    ks = []
    for _ in range(n):
        idx = [rng.randrange(len(a)) for _ in a]
        ks.append(cohen_kappa([a[i] for i in idx], [b[i] for i in idx]))
    ks.sort()
    return [round(ks[int(0.025 * n)], 4), round(ks[int(0.975 * n) - 1], 4)]
