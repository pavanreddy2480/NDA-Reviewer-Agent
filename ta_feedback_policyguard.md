# TA feedback: PolicyGuard overlap, and how to add novelty

> **Historical document.** Kept as a record of its date. The current design is `newdesign.md` (v6; §19 lists the 22 Oct 2026 audit fixes), and the current proposal is `proposal/proposal.tex`.

**TA's comment (9 Oct 2026):** "arxiv 2606.32004 seems very similar to what you guys are trying to do as you guys
mention. The only novelty remaining is applicability-aware retrieval. Do try to add some more novelty to the agentic
framework, maybe taking inspiration from other domains."

**Short answer:** the TA is right. PolicyGuard already does the core of our pipeline: it turns company policy into
rules, finds the relevant clause for each rule, checks it in a structured way and cites evidence. What PolicyGuard
doesn't do is *act*. It only flags problems: it never repairs the draft, never checks whether a fix breaks another
rule, and never looks at the draft the way the other side would. That is where we can add a genuinely new agentic
loop. Section 4 recommends one.

---

## 1. What PolicyGuard does, in plain words

PolicyGuard (Malik, Singh & Azad, arXiv 2606.32004, June 2026) checks NDAs against one company's
negotiation playbook.

**Offline, once per company:**
1. It splits the playbook into self-contained policy units and writes each as a **rulecard**: the issue, the company
   position, and the condition that counts as non-compliant.
2. An LLM "tightens" each rule so it captures the legal effect, not just the wording.
3. Each rule is translated into **logic**: small true/false facts ("atoms") joined by AND/OR/NOT.
4. Each atom becomes a yes/no question that can be answered from clause text.
5. Each rule is tested on a synthetic violating passage. If the engine misses it, an LLM repairs the rule.

**Online, per NDA:**
1. Split the NDA into clauses.
2. For each rule, retrieve the relevant text.
3. The LLM answers the yes/no questions, with evidence.
4. A solver (Z3) evaluates the logic.
5. Output: a list of non-compliance findings (issue, severity, explanation, rule, supporting text).

Key line from the paper: "the LLM does not decide whether the document is compliant; it only grounds local textual
assertions."

**Results:** 95 rules × 5 confidential NDAs = 475 decisions. 93.4% accuracy and 73.7 F1 on non-compliance, against
42.2 F1 for direct prompting. Decisions are also very stable across runs.

**Limitations the authors state themselves:**
- (a) **No cross-rule consistency**: each rule is checked alone, so conflicts between rules are not caught.
- (b) **Absence is not represented first-class**: missing clauses are handled only through yes/no questions.
- (c) One company only.
- (d) The data cannot be released.
- There are also **no redlines**, only a "suggested mitigation" text. **No multi-agent design**, and no latency or
  cost reporting.

---

## 2. Side by side: what they did, what we proposed

| Part of our proposal | PolicyGuard? | Verdict |
|---|---|---|
| Compile company policies into a rule base | Yes (rulecards → logic, with validation and repair) | **Already done**, more rigorously than ours |
| Check the NDA against each rule, cite the clause | Yes, every rule, with evidence | **Already done** |
| Retrieve the relevant clause per rule | Yes | **Already done** |
| Structured checking instead of free LLM judgement (our obligation frames) | Yes (atoms + solver) | **Already done**, arguably stronger |
| Human expert in the loop | Yes | **Already done** |
| Reverse check for missing clauses | Partly (yes/no questions per rule); absence is a stated limitation | Small difference |
| **Only check rules that apply to *this* deal** (applicability by counterparty, data, country) | No: checks all 95 rules every time | **New**: this is what the TA counted |
| Indian law pack | No | Adds more rules, not a new method |
| Multi-agent pipeline (planner, reviewers, verifier) | No | Standard pattern; the brief's own direction D describes it, so the TA doesn't count it |
| Speculative early review | No | Speculative Interaction Agents (2026) already speculate on unfinished input, so the TA doesn't count it |
| Open benchmark (PolicyNDA) | No (private data) | A real contribution, but a *data* contribution, not a method |
| Redlines that fix the draft | No | **Open gap** |
| Catching conflicts *between* rules | No: a stated limitation | **Open gap** |
| Reading the draft as the counterparty would, to find loopholes | No | **Open gap** |

**Why the TA says only applicability is new:**
- The core of our method (compile rules, retrieve, check, cite) is PolicyGuard's method.
- The extras are either standard (multi-agent pipelines), already published elsewhere (speculation), or
  "more of the same" (more rules, more data).
- Only the deal-specific filter changes *how* the checking works.

---

## 3. Ideas from other domains for the agentic part

Each idea starts where PolicyGuard stops: it only detects.

| # | Borrowed from | What the agent does | Why PolicyGuard doesn't cover it | How we measure it (exact ground truth) |
|---|---|---|---|---|
| A | **Software engineering:** automated program repair + regression test suites | A **repairer** writes the smallest redline that fixes each finding, then re-runs **all** rules and the law pack as a test suite. If a fix breaks another rule (e.g. extending a confidentiality term past a policy maximum), it tries again or escalates. | No redlines; no cross-rule consistency (their stated limitation (a)) | Planted defects were made by editing an original clause, so **the original is the gold repair**. Metrics: repair success, **regression rate** (new violations introduced), edit size, senior-review acceptance on a sample |
| B | **Security:** red teaming, fuzzing; military wargaming | An **opposing-counsel agent** reads the draft from the counterparty's side and tries to build concrete **escape scenarios**: "we can use your data for our own product because the residuals clause allows it", "oral disclosures aren't covered, so this meeting wasn't confidential". | PolicyGuard checks the company's checklist; it never asks how the other side could exploit the text | **Loophole recall on planted loopholes.** ContractNLI already labels classic loopholes: *permissible development of similar information*, *permissible acquirement of similar information*, *permissible post-agreement possession*, *non-inclusion of non-technical information*. Scenario validity is checked by a judge validated on human labels |
| C | **Formal methods:** CEGAR (counterexample-guided refinement); also GAN-style attacker vs defender | **A and B in a loop.** The attacker finds a counterexample scenario, the repairer patches the draft, the regression checker verifies nothing else broke, and the attacker tries again. The loop stops when the attacker fails within its budget, or escalates to the senior lawyer. | Detection only, single pass, no adversary, no repair | Everything in A and B, plus **residual defects and loopholes after the loop** vs one-shot repair at the same token budget, and rounds to convergence |
| D | **Medicine:** residency apprenticeship; **ML:** active learning | The copilot asks the senior lawyer only the **highest-value questions** and learns from each answer (e.g. "Singapore law is fine for this partner"), updating rule applicability over a stream of NDAs. This is "knowledge transfer" literally. | Static rules; expert edits are manual | Accuracy against the number of escalations, over a stream of 123 NDAs (learning curve); the senior lawyer is simulated from gold labels |
| E | **Clinical pharmacology:** drug–drug interaction checking | A **rule-interaction checker** finds conflicts *between* requirements (a company rule that demands what Indian law voids, or two rules that can't both be met). | Stated limitation (a) | Planted conflicting rule pairs; conflict recall and precision |

---

## 4. Recommendation: idea C, the counterexample-guided red-team and repair loop

**Why C:**
- **It is new against PolicyGuard on three axes at once:** repair, cross-rule regression checking (their own stated
  limitation), and an adversary. It isn't a tweak of their pipeline.
- **It is genuinely agentic:** several agents with opposed goals, a plan–act–verify loop, a stopping decision and
  escalation. This is exactly what the TA asked for.
- **It matches your original goal** of evaluating "all possible lawsuits and conflicts" a draft could lead to: the
  attacker *is* the lawsuit-finder, framed safely as concrete dispute scenarios.
- **Ground truth stays exact:** gold repairs come from the original clauses, and loopholes are planted or anchored to
  ContractNLI labels.
- **The inspiration is easy to explain to the TA:** "we borrowed CEGAR from formal verification and regression
  testing from program repair".

**What changes in the proposal:**
- **RQ1 stays** (applicability-aware retrieval, the part the TA accepted). The detection pipeline becomes the
  "checker" inside the loop.
- **New RQ2 replaces speculation:** *Does a counterexample-guided loop (opposing-counsel attacker + repairer + full
  regression check) leave fewer violations, omissions and loopholes, and introduce fewer new conflicts, than one-shot
  repair by the same model at the same token budget?*
  - **H2:** residual defects after the loop ≤ half of one-shot repair; regression rate < 5%; ≥ 70% of redlines
    accepted in a blind review of 50.
- **Speculation becomes optional future work.** The TA didn't count it, and dropping it frees the effort the loop
  needs.
- **New ablations:**
  - no attacker (repair + regression only);
  - no regression check (attacker + repair only);
  - one round vs up to three rounds;
  - attacker on the same model vs a different model.
- **Safety stays the same:** redlines are suggestions only, `send_to_counterparty` stays blocked, and attack
  scenarios are internal analysis, never sent anywhere.
- **Cost:** the loop is capped at 3 rounds and runs only on the full system. That is free on Llama in stage 1 and
  about $30 extra on Gemini in stage 2.

**The main risk, and the fix:** the repairer could "game" our own checker (fixing text so the checker passes without
really fixing the problem).
- Fix: score repairs with checks the repairer never sees:
  - gold original clauses;
  - the 5 held-out ContractNLI checks;
  - a separate judge validated on 100 human labels.

**Prior work still to check:**
- LegalSim (arXiv 2510.03405) and AgentCourt (arXiv 2408.08089) simulate adversarial *litigation*, not contract
  drafting, so they are related work, not overlap.
- "Counterexamples as Feedback for Agent Self-Correction" (arXiv 2609.02892) is a general method we should cite.
- I could not read arXiv 2610.11030, a result about agentic redlining, because the site rate-limited me. Someone
  should skim it before the resubmission.

**If you prefer a smaller change:** idea A alone (repair + regression) is the cheapest addition that still fixes
PolicyGuard's stated limitation.
