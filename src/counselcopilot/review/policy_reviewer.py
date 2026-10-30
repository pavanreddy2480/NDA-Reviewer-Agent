"""Policy reviewer with applicability-aware two-way retrieval (design §4, R2-R3; RQ1).

Reverse path (omissions and violations): deal context -> applicable rules -> for each rule,
retrieve the NDA segments most related to it -> check whether the term is there.
Forward path (violations only): each NDA segment -> retrieve related rules -> check them.
A forward hit can never establish an omission, because there is nothing to point at.

The same class runs the RQ1 comparison systems and ablations through `ReviewConfig`:

    Full policy reviewer      reverse + forward, applicability filter on
    no reverse (ablation)     forward only                     -> the clean RQ1 test
    no deal filter (ablation) reverse + forward over all rules
    B4 exhaustive             every rule in the pack, whole NDA in the prompt, no filter
    B4+filter                 every *applicable* rule, whole NDA in the prompt. The fair
                              competitor: same applicability, no retrieval (review problem 3)
    agentic                   full, plus an agent that searches again for any reverse check
                              left unsettled (agentic.py). Field rules are not re-searched

Fairness (review problem 9): every configuration sends its checks to the same `checker_llm`
(the QLoRA model once it exists), so a difference between presets comes from retrieval and
applicability, never from which model answered the checks.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field

from ..data.draft import Draft
from ..llm import LLMClient, PendingBatch
from ..policy.schema import DealContext, LawPack, PolicyPack, Rule, applicability
from ..retrieval.index import Encoder, HybridIndex, Passage, Reranker
from .agentic import EvidenceSearch, search_evidence
from .checker import CheckResult, finding_from_check, run_check
from .fields import extract_field, judge_field_rule
from .applicability import judge_applicability
from .deal_facts import InferredFact, resolve_deal
from .findings import FindingType, Finding, Ledger


@dataclass
class ReviewConfig:
    reverse: bool = True
    forward: bool = True
    applicability_filter: bool = True
    exhaustive: bool = False  # B4: check rules against the whole NDA instead of retrieved segments
    k_segments: int = 12  # NDA segments per reverse check, plus ±1 neighbours (BM25 gold-evidence recall on dev:
    # k=8 0.80, k=12 0.88, k=20 0.95 without neighbours; k=12 with ±1 neighbours 0.948; `cc retrieval --neighbours 1`)
    neighbours: int = 1  # add +-n neighbouring segments around each hit (keeps exceptions with rules)
    forward_rules_per_segment: int = 3
    forward_min_score: float = 4.0  # BM25 score needed for a forward rule hit
    agentic: bool = False  # an agent searches again when a reverse check is left unsettled
    agentic_min_confidence: float = 0.7  # below this a check is unsettled whatever its label; NotMentioned always is
    agentic_max_steps: int = 4  # model calls per search
    agentic_max_segments: int = 8  # new segments per search, before ±neighbours
    max_workers: int = 8
    temperature: float = 0.0  # >0 for seed runs, so seeds give real variance (review problem 10)
    seed: int = 0
    # "model": cards with `applies_when` are judged by the backbone (review/applicability.py), the
    # main system since 25 Oct; "structured": every rule's `applies_if` expression (ablation).
    # Rules without `applies_when` (the law pack, hand-written packs) always use `applies_if`.
    applicability: str = "model"

    @classmethod
    def preset(cls, name: str) -> "ReviewConfig":
        presets = {
            "full": cls(),
            "agentic": cls(agentic=True),
            "no_reverse": cls(reverse=False),
            "no_filter": cls(applicability_filter=False),
            "reverse_only": cls(forward=False),
            "exhaustive": cls(reverse=True, forward=False, applicability_filter=False, exhaustive=True),
            "exhaustive_filtered": cls(reverse=True, forward=False, applicability_filter=True, exhaustive=True),
        }
        return presets[name]


@dataclass
class CheckLog:
    rule_id: str
    direction: str
    result: CheckResult
    agent: EvidenceSearch | None = None  # the search this check set off, if any


@dataclass
class ReviewResult:
    draft_id: str
    findings: list[Finding]
    checks: list[CheckLog] = field(default_factory=list)
    applicable_rules: list[str] = field(default_factory=list)  # under the (completed) deal, every preset
    undecided_rules: list[str] = field(default_factory=list)  # a fact that decides them is still unknown
    deal: DealContext | None = None  # after inferring blank facts
    inferred_facts: list[InferredFact] = field(default_factory=list)
    rules_in_scope: list[str] = field(default_factory=list)  # what this preset checked
    applicability_notes: dict[str, str] = field(default_factory=dict)  # model's rationale per card

    @property
    def n_errors(self) -> int:
        return sum(bool(c.result.error) for c in self.checks)

    @property
    def n_checks(self) -> int:
        return len(self.checks)

    @property
    def n_agent_searches(self) -> int:
        return sum(c.agent is not None for c in self.checks)


def rule_query(rule: Rule) -> str:
    return " ".join([rule.title, rule.check_term, " ".join(rule.keywords)])


class PolicyReviewer:
    def __init__(self, llm: LLMClient, pack: PolicyPack, config: ReviewConfig | None = None,
                 encoder: Encoder | None = None, reranker: Reranker | None = None,
                 law_pack: LawPack | None = None, checker_llm: LLMClient | None = None):
        self.llm = llm  # deal-fact inference and field extraction
        self.checker = checker_llm or llm  # every rule check, in every preset
        self.pack = pack
        self.law_rules = law_pack.as_rules() if law_pack else []
        self.cfg = config or ReviewConfig()
        self.encoder = encoder
        self.reranker = reranker

    # ------------------------------------------------------------------ helpers
    def _applicability(self, deal: DealContext, draft: Draft,
                       seg_index: HybridIndex) -> tuple[dict[str, bool | None], dict[str, str]]:
        """True / False per rule, or None when a fact that decides it is still unknown (the reply
        was unreadable, or the NDA names no governing law). Unknown is never read as False."""
        rules = list(self.pack.rules) + self.law_rules
        structured = deal.model_copy(update={"governing_law": None}) if deal.governing_law == "unknown" else deal
        app = {r.id: applicability(r, structured) for r in rules}
        notes: dict[str, str] = {}
        if self.cfg.applicability == "model":
            judged, notes = judge_applicability(self.llm, rules, deal, draft, seg_index)
            app.update(judged)
        return app, notes

    def _rules_in_scope(self, app: dict[str, bool | None]) -> list[Rule]:
        rules = list(self.pack.rules) + self.law_rules
        if self.cfg.applicability_filter:  # undecided rules are checked rather than dropped
            return [r for r in rules if app[r.id] is not False]
        return rules

    def _read_fields(self, form: DealContext, inferred: list[InferredFact], fields: set[str],
                     draft: Draft, seg_index: HybridIndex) -> dict[str, tuple | Exception]:
        """Each field once per review. When governing law was read from the NDA for applicability,
        the field rule reuses that reading, so the two never disagree (forward-pass audit, point 2).
        A law written on the form is a deal fact, not the NDA's clause, so the clause is still read."""
        values: dict[str, tuple | Exception] = {}
        if "governing_law" in fields and form.governing_law is None:
            f = next((f for f in inferred if f.name == "governing_law" and not f.error), None)
            if f is not None:
                values["governing_law"] = (f.value, f.evidence)
        ids = list(range(len(draft.segments))) if self.cfg.exhaustive else None

        def read(name: str):
            try:
                return name, extract_field(self.checker, name, draft, seg_index, ids=ids)
            except PendingBatch:
                raise
            except Exception as e:  # malformed reply: the field's rules count under check_errors
                return name, e

        values.update(self.llm.map(read, sorted(fields - set(values)), self.cfg.max_workers))
        return values

    def _expand(self, ids: list[int], n_segments: int) -> list[int]:
        out = set(ids)
        for i in ids:
            for d in range(1, self.cfg.neighbours + 1):
                out.update(j for j in (i - d, i + d) if 0 <= j < n_segments)
        return sorted(out)

    def _segment_index(self, draft: Draft) -> HybridIndex:
        return HybridIndex([Passage(str(i), s) for i, s in enumerate(draft.segments)],
                           self.encoder, self.reranker)

    def _unsettled(self, res: CheckResult) -> bool:
        if res.error:  # a failed check says nothing about the NDA, so there is nothing to follow up
            return False
        return res.label == "NotMentioned" or res.confidence < self.cfg.agentic_min_confidence

    # ------------------------------------------------------------------ main entry
    def review(self, draft: Draft, deal: DealContext) -> ReviewResult:
        seg_index = self._segment_index(draft)
        form = deal
        deal, inferred = resolve_deal(self.llm, deal, draft, seg_index)
        app, notes = self._applicability(deal, draft, seg_index)
        rules = self._rules_in_scope(app)
        ledger = Ledger()
        logs: list[CheckLog] = []

        # Field rules are answered by the field extractor in every configuration.
        field_rules = [r for r in rules if r.kind == "field"]
        term_rules = [r for r in rules if r.kind != "field"]

        values = self._read_fields(form, inferred, {r.constraint.field for r in field_rules}, draft, seg_index)

        def do_field(rule: Rule):
            v = values[rule.constraint.field]
            if isinstance(v, Exception):
                f, res = None, CheckResult("NotMentioned", [], 0.0, "", [], error=str(v)[:200])
            else:
                f, res = judge_field_rule(rule, draft.id, *v)
            if f is not None and f.type == FindingType.OMISSION and not (self.cfg.reverse or self.cfg.exhaustive):
                f = None  # forward-only systems cannot report omissions, field rules included
            return [CheckLog(rule.id, "field", res)], f

        # Forward path: segment -> rules. In two-way mode its segments are merged into the
        # rule's reverse check (one call per rule); in forward-only mode it runs on its own
        # and may only report violations.
        forward = (self._forward_candidates(draft, term_rules)
                   if self.cfg.forward and not self.cfg.exhaustive else {})

        def do_reverse(rule: Rule):
            if self.cfg.exhaustive:
                ids, direction = list(range(len(draft.segments))), "exhaustive"
            else:
                hits = seg_index.search(rule_query(rule), k=self.cfg.k_segments)
                ids = self._expand([int(h.passage.id) for h in hits], len(draft.segments))
                direction = "reverse"
                if rule.id in forward:
                    ids, direction = sorted(set(ids) | set(forward[rule.id])), "two_way"
            res = run_check(self.checker, rule.check_term, draft, ids, tag="reverse_check",
                            temperature=self.cfg.temperature, seed=self.cfg.seed)
            checks = [CheckLog(rule.id, direction, res)]
            if self.cfg.agentic and not self.cfg.exhaustive and self._unsettled(res):
                found = search_evidence(self.llm, rule, rule_query(rule), draft, seg_index, ids,
                                        self.cfg.agentic_max_steps, self.cfg.agentic_max_segments,
                                        self.cfg.temperature, self.cfg.seed)
                checks[0].agent = found
                if found.segments:
                    wider = sorted(set(ids) | set(self._expand(found.segments, len(draft.segments))))
                    second = run_check(self.checker, rule.check_term, draft, wider, tag="agentic_check",
                                       temperature=self.cfg.temperature, seed=self.cfg.seed)
                    checks.append(CheckLog(rule.id, "agentic", second))
                    if not second.error:  # a failed second check must not erase what the first found
                        res, direction = second, "agentic"
            return checks, finding_from_check(rule, res, draft.id, direction=direction)

        def do_forward(rule: Rule):
            res = run_check(self.checker, rule.check_term, draft, forward[rule.id], tag="forward_check",
                            temperature=self.cfg.temperature, seed=self.cfg.seed)
            f = finding_from_check(rule, res, draft.id, direction="forward", allow_omission=False)
            return [CheckLog(rule.id, "forward", res)], f

        jobs = [(do_field, r) for r in field_rules]
        if self.cfg.reverse or self.cfg.exhaustive:
            jobs += [(do_reverse, r) for r in term_rules]
        else:
            jobs += [(do_forward, r) for r in term_rules if r.id in forward]

        for checks, f in self.llm.map(lambda j: j[0](j[1]), jobs, self.cfg.max_workers):
            logs += checks
            if f is not None:
                ledger.add(f)

        applicable = [rid for rid, a in app.items() if a is True]
        undecided = [rid for rid, a in app.items() if a is None]
        return ReviewResult(draft.id, ledger.all(), logs, applicable, undecided, deal, inferred,
                            [r.id for r in rules], notes)

    # ------------------------------------------------------------------ forward path
    def _forward_candidates(self, draft: Draft, rules: list[Rule]) -> dict[str, list[int]]:
        if not rules:
            return {}
        rule_index = HybridIndex([Passage(r.id, rule_query(r)) for r in rules], self.encoder, None)
        hits: dict[str, list[tuple[float, int]]] = defaultdict(list)
        for i, seg in enumerate(draft.segments):
            for h in rule_index.search(seg, k=self.cfg.forward_rules_per_segment):
                if self.encoder is not None or h.score >= self.cfg.forward_min_score:
                    hits[h.passage.id].append((h.score, i))
        out: dict[str, list[int]] = {}
        for rid, lst in hits.items():
            top = [i for _, i in sorted(lst, reverse=True)[: self.cfg.k_segments]]
            out[rid] = self._expand(top, len(draft.segments))
        return out
