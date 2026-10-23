# LMA Group Project: shortlist and recommendation

What prop.pdf asks for (summary): one narrow real problem, a testable research question, a small prototype that
combines several of the five capabilities (fine-tuning, RAG, reasoning, agentic, tool calling) with a reason for
each, at least one baseline, an eval set with known ground truth, one metric per capability, an ablation per
capability the RQ depends on, tool-call accuracy and unsafe-action rate for acting systems, an LLM judge only if
validated against human labels, and a compute budget (GPU hours + API cost). Compute must stay small.

Assumed compute (change if yours differs): free Colab / Kaggle T4 GPUs (Kaggle gives ~30 GPU-hours/week) for QLoRA
on a 3B to 8B model, plus about $50 of API credit for a small hosted model.

---

## Recommended: NDA review agent that catches planted inconsistencies (Legal, direction D)

**Research question.** Does a multi-stage review pipeline, where specialist reviewer agents use deterministic
contract tools and must cite clause evidence, catch more risky terms and planted inconsistencies, with fewer false
alarms, than a single-pass review by the same model under the same token budget?

**Data (all public, with ground truth).**
- ContractNLI: 607 real NDAs, 17 fixed hypotheses per NDA (e.g. "confidential info may be shared with
  employees"), each labelled entailed / contradicted / not mentioned, with the evidence spans marked.
  https://arxiv.org/abs/2110.01799
- CUAD: 510 commercial contracts with ~13k expert clause annotations across 41 categories (governing law,
  liability cap, termination, etc.). Useful as extra clause-retrieval corpus and fine-tuning data.
- Your own injected test set: take ~100 held-out NDAs and programmatically plant defects (a defined term used
  inconsistently, conflicting term lengths in two clauses, a broken cross-reference, a governing-law clause that
  clashes with the jurisdiction clause, a one-sided liability shift). Because you plant them, ground truth is exact.
  Keep some clean copies to measure false alarms.

**Why each capability is needed (and its metric).**
| Capability | Role in the system | Metric |
|---|---|---|
| Fine-tuning | QLoRA a small model (Qwen2.5-7B or Llama-3.1-8B) as the per-hypothesis NLI + evidence classifier; RQ-side claim: tuned 7B matches a large prompted model | ContractNLI accuracy / macro-F1, evidence-span F1, vs. prompted large model |
| RAG | Retrieve the relevant clauses inside a long NDA, plus a small "firm playbook" of acceptable clause wording | Evidence recall@k, citation faithfulness (cited span actually supports the claim) |
| Reasoning | Decompose the review into per-issue checks, verify each finding against evidence, self-critique before reporting | Step-level accuracy of intermediate findings, % findings dropped by verifier that were truly false |
| Agentic | Planner routes the NDA to specialist reviewers (definitions, obligations, term/termination, liability), shared state of findings, hands uncertain cases to a lawyer | Planted-defect recall, false-alarm rate on clean NDAs, hand-off precision |
| Tool calling | Deterministic tools: definition extractor, cross-reference resolver, date/number normaliser, clause diff, playbook lookup; a mock "send redline to counterparty" tool that needs approval | Tool-call accuracy, argument validity, error recovery, unsafe/unapproved action rate (must be 0) |

**Baselines.** (1) Single-pass prompt: "review this NDA" with the same model. (2) Plain RAG + same model, no agents
or tools. **Ablations:** remove the verifier, remove tools, replace the tuned model with the untuned one, remove
retrieval (full-context only).

**Compute estimate.** QLoRA on ContractNLI train split: ~2 to 4 T4 GPU-hours per run, 3 runs ≈ 12 hours.
Agent runs: ~200 test NDAs × ~40k tokens × ~6 configurations ≈ 50M tokens; on a small hosted model that is roughly
$20 to $50 (estimate, check current prices), or $0 if you serve the open model yourselves.

**Why it's the pick.** Cleanest ground truth of the options, cheapest to run (text only, no sandbox to host),
every capability has a real job, and "planted-defect detection" is a clear, workshop-style evaluation.
**Risk / fallback:** if the multi-agent pipeline doesn't beat single pass, the result is still reportable; narrow to
the 3 or 4 defect types that work and analyse why the rest fail.

---

## Alternative 2: Incident root-cause agent over real telemetry (Software eng., direction E)

- **RQ:** does a hypothesis-then-verify loop find the root-cause service and fault type more often, with fewer
  unsafe remediation actions, than a standard ReAct tool agent?
- **Data:** RCAEval: 735 labelled failure cases from three microservice systems (Online Boutique, Sock Shop,
  Train Ticket) with metrics, logs and traces, downloadable from Zenodo. https://arxiv.org/abs/2412.17015
  Offline replay means no Kubernetes cluster is needed; tools just query the recorded telemetry.
- **Strengths:** tool calling, agentic and reasoning are very natural; unsafe-action rate via a mock
  rollback/restart tool behind an allow-list.
- **Weaknesses:** RAG needs runbooks/postmortems you write yourselves; fine-tuning is a weaker fit (e.g. a small
  log-anomaly classifier); telemetry wrangling is real engineering work; lots of 2025 papers already do RCA agents.

## Alternative 3: Clinical task agent on a FHIR sandbox (Healthcare, direction C)

- **RQ:** does grounding every turn in the patient record plus an explicit escalation policy complete more tasks
  and miss fewer red-flag cases than a general agent with the same tools?
- **Data:** MedAgentBench: 300 clinician-written tasks, 100 synthetic patients in a Docker FHIR server, with
  reference answers. https://arxiv.org/abs/2501.14654 Add your own injected red-flag scenarios (Synthea patients).
- **Strengths:** ready-made tool environment with ground truth; strong safety story.
- **Weaknesses:** a 2026 paper already fine-tunes small local models on this benchmark
  (https://arxiv.org/abs/2603.06902), so novelty is harder; TAs will scrutinise medical safety more.

---

## Next steps
1. Team picks one (or tells me your real GPU/API budget and I'll re-rank).
2. I draft the full proposal in the section-8 format (title, problem statement, RQ, capability table,
   architecture diagram, eval, compute, risks) for your TA.
