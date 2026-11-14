"""CounselCopilot: the full detection pipeline of proposal Figure 1 (RQ1 "Full" system).

    NDA draft + deal form
      -> deal facts read from the NDA where the form is blank
      -> planner picks reviewers
      -> policy reviewer (two-way, applicability-aware, frames, cross-reference graph)
         law & risk reviewer (US law pack + dispute patterns)
         consistency reviewer (deterministic tools)
      -> shared findings ledger (every finding cites an NDA segment and a rule or statute)
      -> verifier (both citations; unsupported findings dropped)
      -> supported: to the repair loop / report;  approval-gated: approval agent + precedent memory;
         uncertain: senior counsel

Every component can be switched off for the ablations of proposal §7 through `PipelineConfig`
(`PipelineConfig.ablation(name)`), and every model call goes to the same backbone, with rule
checks on `checker_llm` (the QLoRA model once it exists) in every configuration, so differences
come from the design and not from which model answered.

`review()` returns a `PipelineResult`, which has the fields experiments/rq1.py reads from a
`ReviewResult`, so the RQ1 runner scores the pipeline, the reviewer presets and the baselines the
same way.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace

from ..data.draft import Draft
from ..llm import LLMClient
from ..policy.schema import DealContext, LawPack, PolicyPack
from ..retrieval.index import HybridIndex, Passage
from ..review.consistency import check_consistency
from ..review.deal_facts import resolve_deal
from ..review.findings import Finding, FindingType, Ledger
from ..review.law_reviewer import LawReviewer
from ..review.policy_reviewer import PolicyReviewer, ReviewConfig, ReviewResult
from ..review.verifier import Verdict, Verifier
from .handoff import ApprovalDesk, HandoffResult
from .memory import PrecedentMemory
from .planner import Plan, Planner


@dataclass
class PipelineConfig:
    review: ReviewConfig = field(default_factory=lambda: replace(ReviewConfig.preset("full"), frames=True, xref=True))
    planner: str = "model"  # model | rules | fixed
    verifier: bool = True
    memory: bool = True
    tool_agent: bool = True
    consistency: bool = True
    tool_error_rate: float = 0.0  # injected tool errors (proposal §5: recovery from 10%)
    seed: int = 0

    ABLATIONS = ("full", "no_reverse", "no_filter", "no_frames", "no_verifier", "fixed_pipeline", "no_xref",
                 "no_memory", "no_tool_agent", "structured_applicability", "tool_errors")

    @classmethod
    def ablation(cls, name: str) -> "PipelineConfig":
        """One change from the full system (proposal §7 ablations row)."""
        c = cls()
        r = c.review
        if name == "full":
            pass
        elif name == "no_reverse":
            c.review = replace(r, reverse=False)
        elif name == "no_filter":
            c.review = replace(r, applicability_filter=False)
        elif name == "no_frames":
            c.review = replace(r, frames=False)
        elif name == "no_xref":
            c.review = replace(r, xref=False)
        elif name == "structured_applicability":
            c.review = replace(r, applicability="structured")
        elif name == "no_verifier":
            c.verifier = False
        elif name == "fixed_pipeline":
            c.planner = "fixed"
        elif name == "no_memory":
            c.memory = False
        elif name == "no_tool_agent":
            c.tool_agent = False
        elif name == "tool_errors":
            c.tool_error_rate = 0.1
        else:
            raise KeyError(f"unknown ablation {name!r}; choose from {cls.ABLATIONS}")
        return c


@dataclass
class PipelineResult(ReviewResult):
    plan: Plan | None = None
    all_findings: list[Finding] = field(default_factory=list)  # before the verifier
    verdicts: list[Verdict] = field(default_factory=list)
    handoff: HandoffResult | None = None
    unscored_findings: list[Finding] = field(default_factory=list)  # consistency / dispute risk: no gold

    @property
    def supported(self) -> list[Finding]:
        return [f for f in self.findings if f.verified is True]


class CounselCopilot:
    def __init__(self, llm: LLMClient, pack: PolicyPack, law_pack: LawPack | None = None,
                 config: PipelineConfig | None = None, checker_llm: LLMClient | None = None,
                 memory: PrecedentMemory | None = None, encoder=None, reranker=None):
        self.llm = llm
        self.checker = checker_llm or llm
        self.pack, self.law_pack = pack, law_pack
        self.cfg = config or PipelineConfig()
        self.memory = memory if (memory is not None and self.cfg.memory) else PrecedentMemory()
        self.policy = PolicyReviewer(llm, pack, self.cfg.review, encoder, reranker, law_pack=None,
                                     checker_llm=checker_llm)
        self.law = (LawReviewer(llm, law_pack, self.cfg.review, checker_llm, encoder, reranker)
                    if law_pack is not None else None)
        self.planner = Planner(llm, self.cfg.planner)
        rules = list(pack.rules) + (law_pack.as_rules() if law_pack else [])
        self.verifier = Verifier(llm, rules) if self.cfg.verifier else None
        self.desk = ApprovalDesk(llm, pack, law_pack, self.memory, agent=self.cfg.tool_agent,
                                 error_rate=self.cfg.tool_error_rate, seed=self.cfg.seed)

    def review(self, draft: Draft, deal: DealContext) -> PipelineResult:
        index = HybridIndex([Passage(str(i), s) for i, s in enumerate(draft.segments)])
        completed, inferred = resolve_deal(self.llm, deal, draft, index)
        plan = self.planner.plan(draft, completed, law_available=self.law is not None)

        # the reviewers get the completed deal, so facts are read from the NDA once
        pol = self.policy.review(draft, completed)
        results = [pol]
        if "law" in plan.reviewers and self.law is not None:
            results.append(self.law.review(draft, completed))
        ledger = Ledger()
        for r in results:
            ledger.extend(r.findings)
        if "consistency" in plan.reviewers and self.cfg.consistency:
            ledger.extend(check_consistency(draft))
        found = ledger.all()

        verdicts: list[Verdict] = []
        if self.verifier is not None:
            verdicts = self.verifier.verify_all(draft, found)
            kept = [v.finding for v in verdicts if v.verdict != "unsupported"]
        else:
            kept = [f.model_copy(update={"verified": True}) for f in found]
        uncertain = [f for f in kept if f.verified is None]
        handoff = self.desk.handle([f for f in kept if f.type == FindingType.APPROVAL_NEEDED], completed, uncertain)

        scored = [f for f in kept if not f.rule_id.startswith(("CONS-", "RISK-"))]
        unscored = [f for f in kept if f.rule_id.startswith(("CONS-", "RISK-"))]
        checks = [c for r in results for c in r.checks]
        app = {rid for r in results for rid in r.applicable_rules}
        und = {rid for r in results for rid in r.undecided_rules}
        notes = {k: v for r in results for k, v in r.applicability_notes.items()}
        return PipelineResult(
            draft.id, scored, checks, sorted(app), sorted(und), pol.deal or completed, inferred,
            [rid for r in results for rid in r.rules_in_scope], notes,
            plan=plan, all_findings=found, verdicts=verdicts, handoff=handoff, unscored_findings=unscored)

    def detect(self, draft: Draft, deal: DealContext) -> list[Finding]:
        """Findings only (for the regression checker of the repair loop)."""
        res = self.review(draft, deal)
        return res.findings + res.unscored_findings
