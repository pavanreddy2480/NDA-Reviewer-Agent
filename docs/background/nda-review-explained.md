# NDA Review Agent: explained against the assignment

This explains the idea in docs/archive/ideas/01-nda-review-agent.md (that file is unchanged). Section numbers like "§7" refer to docs/course/project-brief.pdf.

---

## 1. The idea in plain words

**Who it's for:** a junior lawyer or a startup founder who receives an NDA (non-disclosure agreement) from another
company and has to decide whether it is safe to sign.

**The problem:** NDAs look standard but often hide problems:
- **Risky terms:** "Confidentiality lasts forever", "You can't hire any of our employees for 5 years", "Disputes are
  settled in a court in another country".
- **Internal inconsistencies:** "Confidential Information" is defined one way in clause 1 and used differently in
  clause 7; clause 3 says the agreement lasts 2 years but clause 9 says 3; clause 5 refers to "Section 12", which
  doesn't exist.

A single read-through by a person or by ChatGPT misses many of these, especially inconsistencies that span two
clauses far apart. It also produces false alarms that waste a lawyer's time.

**What we build:** an AI agent that reviews an NDA in stages, like a small law firm:
1. A **planner** splits the review into specialist checks.
2. **Specialist reviewers** each look for one kind of problem (definitions, obligations, term and termination,
   liability and jurisdiction). They use **tools** that check things precisely (find every place a defined
   term is used, resolve "Section 12" references, normalise dates and durations).
3. Every finding must **cite the exact clause** it is based on (RAG).
4. A **verifier** re-checks each finding against the cited text and drops weak ones.
5. Uncertain findings are **handed to a human lawyer** instead of being stated as fact.
6. The output is a list of issues, each with the clause, an explanation and a severity rating.

**What we prove (the research part):** does this multi-stage, tool-using pipeline catch more real problems with
fewer false alarms than asking the same model to review the NDA in one go?

---

## 2. How it meets each requirement in the assignment

### §1 "Research oriented, not just another chatbot or RAG app"
The deliverable is an experiment, not an app: a clear research question, a method, a test set with known
answers, and evidence for or against the hypothesis.

### §2 The five capabilities (each needs a reason and a metric)
| Capability | Why this problem needs it | How we measure it |
|---|---|---|
| **Fine-tuning** | Checking all 17 standard NDA questions on every contract with a large model is slow and costly. A small model (Qwen2.5-7B or Llama-3.1-8B) tuned with QLoRA does this narrow task cheaply. This tests the brief's own example: "a tuned small model matches a much larger prompted model". | Accuracy and macro-F1 on ContractNLI's test split; small tuned model vs large prompted model |
| **RAG** | NDAs are long, and every claim must be backed by the exact clause so a lawyer can check it. We also retrieve from a small "playbook" of acceptable clause wording to judge what counts as risky. | Evidence recall (did we retrieve the right clause?) and citation faithfulness (does the cited clause actually support the claim?) |
| **Reasoning** | Finding an inconsistency means comparing two clauses and reasoning about them, for example that "2 years" in clause 3 conflicts with "36 months" in clause 9. The verifier also self-critiques each finding. | Accuracy of each intermediate finding, and how many verifier rejections were truly false (we analyse the steps, not just the final answer, as §2 requires) |
| **Agentic** | The planner decides which reviewers to run, reviewers share a findings list, and the system decides when to hand off to a human. | Recall of planted defects, false-alarm rate on clean NDAs, and precision of hand-offs to the human |
| **Tool calling** | Language models are bad at exact bookkeeping, so deterministic tools do it: a defined-term finder, a cross-reference resolver, a date and number normaliser, a clause diff and a playbook lookup. There is also a mock "send redline to counterparty" tool that must never run without approval. | Tool-call accuracy, valid arguments, recovery after errors, and the **unsafe or unapproved action rate** (target 0, required by §7) |

### §3 Domain
Legal, which is one of the listed domains.

### §4 Scope "narrow: one contract type"
One contract type: NDAs only.

### §5 Compute "keep it small"
No large-model training. Only a QLoRA fine-tune of a 7–8B model and API calls to a small hosted model.
See section 5 below for the budget.

### §6 Safety for the domain
- Only public contracts, so no client data.
- The agent never sends anything outside: the "send redline" tool is a mock behind an approval step.
- The output is framed as an assistant to a lawyer, not legal advice. Uncertain findings go to a human.

### §7 Minimum evaluation expectations
| Requirement | How we meet it |
|---|---|
| At least one baseline | (1) Same model, single-pass "review this NDA" prompt. (2) Plain RAG with the same model, no agents or tools. |
| Small, carefully designed eval set with known ground truth | ContractNLI test labels, plus about 100 NDAs with defects **we planted ourselves**, so we know exactly what should be found. Some NDAs are left clean to measure false alarms. |
| At least one metric per capability | See the table in §2 above. |
| Ablation of each capability the research question depends on | Remove in turn: the verifier, the tools, retrieval (paste the full text instead), and the fine-tuned model (swap in the untuned one). |
| Tool-call accuracy and unsafe-action rate | Measured on every run. |
| Qualitative examples | Show tricky cases, such as a definition that changes meaning halfway through the contract. |
| Failure analysis | Report which defect types the system still misses, and why. |
| LLM judge only if validated | Main metrics are exact matches against planted defects, so no judge is needed for them. If we use a judge for explanation quality, we check it against about 100 human labels. |

---

## 3. Datasets (all public, free)

### ContractNLI (main dataset)
- **What it is:** 607 real NDAs collected from the internet (EDGAR filings and other sources), annotated by experts.
- **Labels:** for each NDA, 17 fixed questions, such as "Does the receiving party have to destroy confidential
  information when the agreement ends?" or "Can confidential information be shared with employees?". Each is
  labelled **entailed / contradicted / not mentioned**, with the exact sentences that support the label.
- **Splits:** about 423 train, 61 dev and 123 test documents.
- **Used for:** fine-tuning the small model, testing evidence retrieval and citation accuracy, and as the clean
  base for planting defects.
- Paper: https://arxiv.org/abs/2110.01799 (Koreeda & Manning, Findings of EMNLP 2021). Data from the authors'
  project page (stanfordnlp.github.io/contract-nli).

### CUAD (Contract Understanding Atticus Dataset, supporting dataset)
- **What it is:** 510 commercial contracts with more than 13,000 expert clause labels across 41 categories (governing
  law, non-compete, cap on liability, termination for convenience, and others).
- **Used for:** building the clause library and "playbook" that RAG retrieves from, and extra training data for
  spotting risky clause types.
- Paper: https://arxiv.org/abs/2103.06268 (Hendrycks et al., NeurIPS 2021 Datasets track). Available on Hugging
  Face and atticusprojectai.org/cuad.

### Our planted-defect test set (we create it; this is a contribution)
We take about 100 held-out ContractNLI NDAs and insert defects with a script, recording exactly what and where.
| Defect type | Example |
|---|---|
| Inconsistent definition | "Confidential Information" includes oral disclosures in clause 1 but clause 6 says "written information only" |
| Conflicting durations | Clause 3: "term of two (2) years"; clause 11: "obligations survive for 36 months" |
| Broken cross-reference | "subject to Section 14", but the NDA has 12 sections |
| Jurisdiction clash | Governing law is New York, but disputes go to the courts of Delaware with no reason given |
| One-sided risk shift | Mutual obligations quietly made one-way, or an unusually broad non-solicit clause added |

About 30% of the NDAs stay clean, so we can measure false alarms. Because we planted every defect, ground truth
is exact, with no human labelling needed.

---

## 4. Research question, hypothesis and success criteria

- **Research question:** Does a multi-stage review pipeline (specialist reviewer agents plus deterministic tools
  plus a verifier, all citing clauses) catch more planted inconsistencies and risky terms, with fewer false alarms,
  than a single-pass review by the same model under the same token budget?
- **Hypothesis:** the pipeline improves defect recall, especially for cross-clause defects, while the verifier
  keeps the false-alarm rate at or below the baseline.
- **Second, smaller question:** can a QLoRA-tuned 7B model match a large prompted model on ContractNLI's
  17-question classification?
- **Main metrics:** defect recall, false alarms per clean NDA, F1, and citation faithfulness. Also tool-call
  accuracy and unsafe-action rate.

---

## 5. Compute and budget (§5 asks for this; TAs may reject without it)

These are estimates; check current prices before submitting.

| Item | Hardware or service | Amount |
|---|---|---|
| QLoRA fine-tune of a 7B model on ContractNLI | Free Google Colab or Kaggle T4 GPU (Kaggle allows about 30 GPU-hours a week) | about 2–4 hours per run × 3 runs ≈ 12 GPU-hours |
| Agent experiments | Small hosted LLM API, or the open model served locally | about 200 test NDAs × about 40k tokens × 6 configurations (2 baselines, full system, 3+ ablations) ≈ 50M tokens |
| API cost | | roughly $20–50 with a small hosted model, or $0 if fully local |
| Experiment runs | | about 6 configurations × 2 seeds |

---

## 6. Expected novelty (what is new)
- A **planted-defect benchmark for NDAs** with exact ground truth for cross-clause inconsistencies. Existing
  datasets label single clauses, not conflicts between clauses.
- A **controlled comparison**: multi-agent plus tools versus single pass, under the same model and token budget,
  with an ablation for each component.
- Evidence on whether a **small fine-tuned model** can replace a large one for the per-clause checks.

## 7. Risks and fallback plan
| Risk | Fallback |
|---|---|
| The pipeline doesn't beat single pass | Still a reportable result. Narrow to the defect types where it helps and analyse why it fails on the rest. |
| Fine-tuned model underperforms | Report the gap and use the prompted model inside the pipeline. The fine-tuning comparison remains a finding. |
| Planted defects look unrealistic | Have a teammate check a sample by hand, and phrase defects using real clause wording from CUAD. |
| API budget runs out | Switch to a local open model (Qwen2.5-7B) on Kaggle GPUs. |

## 8. Checklist against the "final proposal must contain" list (§8)
| Required item | Where it's covered |
|---|---|
| Project title | "Catching hidden conflicts in NDAs: multi-stage tool-using review vs single-pass LLM review" |
| Domain and target user | Section 1 |
| Problem statement (5–8 sentences) | Section 1, "The problem" |
| Research question | Section 4 |
| Why it matters in this domain | NDAs are signed constantly, often without a lawyer, and missed conflicts create real legal risk |
| What is missing in existing approaches | Single-pass review misses cross-clause conflicts. Existing datasets don't test them. |
| Capabilities and why each is needed | Section 2, §2 table |
| Idea and architecture (diagram encouraged) | Section 1, "What we build" (draw the planner, reviewers, tools, verifier and hand-off as boxes) |
| Expected novelty | Section 6 |
| Dataset or environment | Section 3 |
| Baselines | Section 2, §7 table |
| Metrics, including capability and safety metrics | Sections 2 and 4 |
| Compute plan | Section 5 |
| Risks and fallback | Section 7 |
