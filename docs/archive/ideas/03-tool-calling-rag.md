# Option 3: Tool calling + RAG focused ideas

Earlier options stay in docs/archive/ideas/01-nda-review-agent.md (NDA review) and docs/archive/ideas/02-speculative-tools.md.
Assumed compute, as before: free Colab/Kaggle T4 + roughly $50 of API credit. Cost numbers are estimates; check
current model prices.

Honest context: in 2026 almost every "tool calling + RAG" angle has some prior paper. For a course project
(the brief says "workshop-level"), a clear research question in a specific domain, a clean eval set with known
answers, and good ablations matter more than being first. Each idea below lists the closest prior work so the
related-work section is easy to write.

---

## Idea A (recommended): Campus helpdesk agent that checks policy against records before it answers or acts

**Domain & user.** Institute management / LMS (both on the brief's list). Students asking things like "Can I still
drop CS201 without a W grade?", "Am I eligible for the scholarship renewal?", "Register me for the elective lab".

**Problem.** The right answer needs two sources at once: the rule lives in the handbook (text, so RAG) and the facts
live in the student's records (database, so tool calls). Plain RAG states the rule but guesses the facts; a plain
tool agent reads the facts but misremembers the rule. When a policy has an exception or the handbook is out of
date compared with the database, both fail quietly. Acting (registering, filing a request) on a wrong eligibility
check is an unsafe action, and an agent with database tools can leak another student's records.

**Research question.** Does an agent that (1) retrieves the governing policy clause, (2) turns it into an explicit
checklist of conditions, (3) checks each condition with scoped database tool calls, and (4) answers only with
evidence for every condition (or abstains), give more correct answers and take fewer unsafe or unauthorised
actions than plain RAG or a ReAct agent with the same tools and token budget?

**Capabilities.**
| Capability | Job | Metric |
|---|---|---|
| RAG (main) | Retrieve the governing clause, including exceptions and amendments | Clause recall@k, citation faithfulness, abstention accuracy on unanswerable questions |
| Tool calling (main) | Read-only SQL/record tools scoped to the logged-in student; write tools (register, drop, file request) behind confirmation | Tool-call accuracy, argument validity, error recovery, unauthorised data access rate, unconfirmed write rate (target 0) |
| Reasoning | Policy turned into explicit conditions, each verified; deadline and credit arithmetic | Per-condition accuracy (you have ground truth for each), where chains break |
| Agentic | Multi-turn: ask a clarifying question, act, hand off to a human advisor when policy is ambiguous | Task success on action tasks, hand-off precision/recall |
| Fine-tuning | QLoRA a 1.5B to 3B model as the source router (docs / DB / both / abstain) or as text-to-SQL for your schema | Router accuracy vs prompted large model; SQL execution accuracy |

**Data / environment.**
- Policy corpus: one real, public academic regulations handbook (your own institute's is ideal, it is the "one
  course / one workflow" scope the brief asks for). Add a few amendment notices that override older clauses to
  create real conflicts.
- Records: a synthetic SQLite database (students, enrolments, grades, fees, deadlines) generated with Faker. You
  generate the questions from templates and compute the true answer with SQL plus the rule, so ground truth is
  exact. Target ~300 questions, ~60 action tasks, ~50 privacy probes ("show me Rahul's grades").
- External validity (public benchmarks): TAT-QA and FinQA (questions needing both a table and text), BIRD mini-dev
  (500 text-to-SQL questions) for the SQL tool.

**Baselines.** Plain RAG (no tools). ReAct agent with the same tools and no checklist step. **Ablations:** no
retrieval, no condition-checking step, no tool scoping, untuned vs tuned router.

**Closest prior work.** Hybrid-source routing on TAT-QA/FinQA (https://arxiv.org/abs/2510.02388, reports low F1, so
there is headroom). Policy-compliance verification for tool agents (https://arxiv.org/abs/2603.20449,
https://arxiv.org/abs/2604.15505). Your difference: education/admin domain, policy-vs-record conflicts, and
privacy-scoped tools measured together.

**Compute.** QLoRA router or text-to-SQL: 2 to 4 T4 GPU-hours per run, ~3 runs. Agent eval: ~400 items × 5
configurations × ~15k tokens ≈ 30M tokens, roughly $15 to $40 with a small hosted model.

**Risks / fallback.** Writing the handbook-to-question generator takes real effort, so start with 3 or 4 policy
areas (add/drop, prerequisites, fees, scholarships). If the checklist step doesn't help, the per-condition error
analysis is still a result.

---

## Idea B (cheapest, cleanest numbers): Tools change, does retrieval or fine-tuning keep the agent correct?

**Domain & user.** Software engineering: an internal API platform whose endpoints keep changing (renamed
parameters, new required fields, unit changes such as dollars to cents, deprecated endpoints).

**Research question.** When tool schemas drift after a model was tuned on them, does retrieving the current tool
docs and changelog plus repairing calls from error messages recover accuracy better than a LoRA-tuned small model,
and which kinds of drift does each fix? Does a tuned model "confidently" call the old schema and cause unsafe
actions (e.g. charging 100x because of a unit change)?

**Capabilities.** Tool calling (main: accuracy, argument validity, recovery after an error, unsafe call rate),
RAG (main: retrieve current schema and changelog entries; doc-retrieval recall), fine-tuning (QLoRA a 1.5B to 7B
model on the old schemas), reasoning (diagnose the error message before retrying; analyse diagnosis steps),
agentic (multi-turn tasks with retries and stopping when unsure).

**Data.** Berkeley Function Calling Leaderboard (BFCL, open source, includes multi-turn tasks) plus your own
programmatically drifted copies of its tools, so the correct call after drift is known exactly. Salesforce
xLAM/APIGen function-calling data for the fine-tune. ToolEVO's ToolQA-D as a second test set.

**Baselines.** Prompted model with old docs. Tuned model without retrieval. **Ablations:** no changelog, no error
feedback, drift type by drift type.

**Closest prior work.** ToolEVO, Learning Evolving Tools (ICLR 2025, https://arxiv.org/abs/2410.06617) trains
with MCTS for tool changes. Your difference: a cheap, controlled retrieval-vs-fine-tuning comparison with a
safety metric for silent semantic drift (units, meaning changes), which errors don't reveal.

**Compute.** QLoRA: 3 to 5 T4 GPU-hours per run. Eval: ~1,600 drifted cases × 6 configs × ~3k tokens ≈ 30M
tokens, roughly $15 to $30, or nearly free with a local 7B model.

**Risk.** Weaker "real domain" story than Idea A; a TA may push for a more concrete user.

---

## Ideas I'd avoid (too crowded for the effort)
- Tool retrieval over huge MCP tool libraries: MCP-Zero (https://arxiv.org/abs/2506.01056), LiveMCPBench
  (https://arxiv.org/abs/2508.01780), HumanMCP (https://arxiv.org/abs/2602.23367) and more.
- Prompt-injection defences for RAG/tool outputs (AgentDojo-style): many defence papers already.
- Generic "when to retrieve" agentic RAG (Self-RAG, Search-R1 lineage).

## Comparison
| | A: Campus helpdesk | B: Tool drift | NDA review | Speculative tools |
|---|---|---|---|---|
| Tool calling + RAG as core | Both, strongly | Both, strongly | RAG strong, tools moderate | Tools strong, RAG weak |
| Fits brief's domain list | Yes (institute/LMS) | Software eng. | Legal | Weak |
| Ground truth | Exact (SQL-computed) | Exact (drift is planted) | Exact (planted) | Exact |
| Novelty risk | Medium | Medium | Medium | High |
| Build effort | Highest | Lowest | Medium | Medium |
