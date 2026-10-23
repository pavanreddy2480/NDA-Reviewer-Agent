# Is CounselCopilot good enough? A check against docs/course/project-brief.pdf and the TA's review

Checked on 9 Oct 2026 against `docs/course/project-brief.pdf`, the TA's PolicyGuard comment, and the current `docs/design/design.md` (v5) and
`docs/proposal/proposal.pdf` (red-team and repair loop version).

## Verdict

**Yes, it meets what the brief asks for, and it answers the TA's comment. Three weak spots should be fixed before
resubmitting (see the end).** The project is not "novel" in the sense of a brand-new algorithm. The brief does not ask
for that. It asks for a novel *approach* whose contribution comes from how you combine and study the capabilities, and
for a project "distinct enough to support a potential workshop-level submission".

## How docs/course/project-brief.pdf defines novelty, and how we match it

| What the brief says (quoted) | What it means | CounselCopilot |
|---|---|---|
| "Your task is not simply to build another chatbot or RAG application … propose a novel approach, build a small prototype, and evaluate whether the idea helps." (§1) | The novelty is in the approach plus the evidence, not the app | ✅ Two testable approaches (applicability-aware retrieval; red-team and repair loop), each with baselines and ablations |
| "Your research contribution should come from how you combine and study the capabilities." (§1) | Novelty = the *combination* and a *study* of it | ✅ The loop needs all five capabilities working together. The study compares it with one-shot repair and Self-Refine at equal budget |
| "The contribution should come from system design, reasoning, data construction, retrieval, memory, tool design, agent architecture or evaluation." (§5) | Data and evaluation count as contributions | ✅ **Agent architecture** (the loop), **retrieval** (applicability), **data construction** (PolicyNDA, open), **evaluation** (exact gold repairs; regression rate) |
| "Adding a capability only because it appears on this list does not count." (§2) | Each capability must be needed and measured | ✅ Each has a reason and a metric (proposal §5); the planner and verifier have their own ablations |
| "These ideas might not be novel … building the system alone is not enough." (§4) | Copying a listed direction is not enough | ⚠️ Our detection pipeline *is* close to direction D and to PolicyGuard. That is exactly the TA's point. Our novelty must rest on the loop and the applicability filter, not on the pipeline. The proposal now says so |
| Example research questions (§4): "does [X] … under the same token budget", "does a hypothesis-driven investigation loop with evidence checking find the root cause more often … than a standard tool-using agent?" | The expected *shape* is a comparative question at equal cost | ✅ RQ2 has exactly this shape: loop vs one-shot vs Self-Refine, same model, same budget. The loop is also the brief's direction E (hypothesis → evidence check → act) moved to legal drafting, which is the "inspiration from other domains" the TA asked for |
| "The review checks … research-oriented, feasible within the available compute and time, safe for its domain, and distinct enough to support a potential workshop-level submission." (§6) | Four tests: research, feasible, safe, distinct | Research ✅. Safe ✅ (mock actions, suggestions only, no lawyer claims). Distinct ✅ (three things PolicyGuard lacks: repair, an adversary, cross-rule regression checking; plus an open benchmark). **Feasible ⚠️**, because the scope is now large; see fix 2 |
| "TAs may ask you to … strengthen the novelty" (§6) | The TA's comment is a standard request to strengthen, not a rejection | ✅ We strengthened the agentic part directly, as asked |
| "Keep the scope narrow: … one contract type" (§4) | Narrow | ✅ NDAs only, India only, 3 policy packs |
| Minimum evaluation list (§7): baseline, known ground truth, metric per capability, ablations, tool-call accuracy, unsafe-action rate, qualitative cases, failure analysis, validated judge | Checklist | ✅ All present. PolicyGuard-style checking is baseline B4, which matches "baselines can range from existing systems" |

## Against the TA's comment specifically

**TA:** "the only novelty remaining is applicability-aware retrieval. Do try to add some more novelty to the agentic
framework, maybe taking inspiration from other domains."

- **Agentic framework:** the loop is a new multi-agent design. Agents with opposed goals (attacker vs repairer), a
  shared checker, a stopping rule and escalation.
- **Inspiration from other domains:** CEGAR from formal verification and regression testing from automated program
  repair. Both are named in the proposal.
- **Clearly outside PolicyGuard:** PolicyGuard only flags. It never repairs, never attacks, and its authors list
  cross-rule consistency as an open problem. Our regression checker targets exactly that problem.

**Likely TA follow-ups, and our answers:**
- "Isn't this just Self-Refine?" No. Self-Refine is our baseline R2, and the RQ tests whether the adversary and the
  regression check add anything beyond plain iteration.
- "How do you know a repair is right?" Every planted defect came from editing an original clause, so the original is
  the gold repair. We never score with the loop's own checker.

## Three weak spots to fix before resubmitting

1. **The attacker must be shown to add something the rule checker can't.** Right now some "natural loopholes" (e.g.
   residuals-type carve-outs) can also be written as policy rules. If a rule already covers a loophole, the checker
   finds it and the attacker looks redundant.
   - Fix: plant a set of loopholes that **no policy rule covers**, and report attacker recall on those separately.
     This is the honest test of the adversary.
2. **Scope versus feasibility.** Two RQs, a 4-baseline RQ1, a 3-system RQ2, many ablations and a policy-size sweep
   is a lot for one semester. The brief explicitly checks "feasible within … time".
   - Fix: mark a **core** set (RQ1 against B2 and B4 plus the reverse-retrieval ablation; RQ2 loop vs R1 and R2)
     and move the rest to **stretch**: the size sweep, the planner ablation, the different-model attacker and the
     Gemini Pro reference runs.
3. **Who judges the redlines.** "≥70% accepted in blind review" by teammates who aren't lawyers is weak evidence.
   - Fix: ask one law student or faculty member to rate the 50-NDA sample. If that isn't possible, rename the
     metric to what it is: "teammate acceptance against the gold clause". The main RQ2 metrics are exact anyway.

**Also still open from before:** skim arXiv 2610.11030 (agentic redlining), which couldn't be read on 9 Oct, and
"Counterexamples as Feedback for Agent Self-Correction" (arXiv 2609.02892), so the loop is clearly distinguished from
both in related work.
