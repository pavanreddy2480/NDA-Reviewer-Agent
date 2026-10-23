# Option 2: Speculative tool calling (draft assessment)

Initial pick (NDA review agent) is kept in project_pick.md. This file is the second candidate.

## The idea in one line
While the main agent is still thinking (or the user is still talking), a cheap predictor guesses the next tool
call and runs it early. If the agent then makes that call, the result is already there and the wait disappears.
If the guess was wrong, the result is thrown away.

## Honest verdict
Good, measurable, cheap topic, but **crowded**. A quick search (Sep 2026) found at least these:

| Paper | What it already covers |
|---|---|
| Speculative Actions (ICLR 2026 oral) https://arxiv.org/abs/2510.04371 | The general framework: fast model guesses next action, verify before commit. Up to 55% next-action accuracy, up to 20% latency cut. |
| PASTE / Act While Thinking https://arxiv.org/abs/2603.18897 | Pattern-based prediction of tool calls in the serving system. 43.5% faster task completion. |
| Speculate with Memory https://arxiv.org/abs/2607.12236 | Retrieval/episodic memory to improve guesses (the "RAG" angle). Only speculates read-only tools. τ²-bench, WebArena, ALFWorld, HotpotQA. |
| Self-Speculating Agents https://arxiv.org/abs/2607.25816 | Fine-tunes (SFT + RL) a 4B model to predict its own next call (the "fine-tuning" angle). Hit@1 44 to 61 on τ-bench, HotpotQA. |
| Speculative Interaction Agents https://arxiv.org/abs/2605.13360, Tool-intent stabilization https://arxiv.org/abs/2606.20113 | Guessing tool calls from a partial user utterance (the "voice" angle). |
| Atomix https://arxiv.org/abs/2602.14849, Ghost Tool Calls https://arxiv.org/abs/2606.02483 | Side effects and privacy of speculative calls (the "safety" angle). |

So "we built speculative tool calling" will not pass as novel. You need one narrow question the above leave open.

Two other concerns against prop.pdf:
- **Domain.** The brief wants a real problem in a domain. Speculation is a systems technique, so frame it as a
  domain problem where latency hurts, e.g. a **voice customer-service agent** (dead air on a phone call).
- **Capability fit.** Tool calling, agentic and fine-tuning fit naturally. RAG and reasoning need a real job or
  they look bolted on (the brief says that "does not count").

## A version I think a TA would accept
**Title (working):** Policy-aware speculative tool calling for a voice customer-service agent.

**Domain & user.** Airline / retail support agent (τ-bench / τ²-bench domains), phone callers who hear silence
while tools run.

**Research question.** Can a small LoRA-tuned "drafter" that is told the domain policy (which tools are safe to
run early, which need the user's confirmation) cut the caller's waiting time as much as a large prompted
drafter, while keeping task success the same and never executing, or nudging the agent into, a write action the
user did not confirm?

**The part that is less covered:** most prior work either only speculates read-only calls or treats safety as a
systems/transaction problem. The open question here is behavioural: when speculative results are shown to the
agent (the "lossy" mode that gives the bigger speed-ups), do they **anchor** the agent into actions it would not
otherwise take, i.e. more policy violations? Please treat this as "not found in a quick search", not as
confirmed novelty; the team should do a proper related-work pass before proposing.

**Capabilities and metrics.**
| Capability | Job | Metric |
|---|---|---|
| Tool calling (core) | Drafter predicts tool name + arguments; gate runs only allowed ones | Hit@1 (exact tool+args), tool-name accuracy, argument validity, wasted calls per task, unsafe speculative execution rate (target 0) |
| Fine-tuning | QLoRA a 0.5B to 1.5B drafter (Qwen2.5) on recorded trajectories | Hit@1 vs prompted large drafter and vs a frequency/transition-table heuristic; drafter latency |
| Agentic | Multi-turn support agent with state (bookings, orders), confirmation step before writes | Task success (pass^k), policy-violation rate, with vs without speculation |
| RAG | Retrieve the relevant policy section for the drafter's gate (and similar past trajectories as few-shot) | Gate accuracy (allowed vs blocked correctly), Hit@1 with vs without retrieval |
| Reasoning | Drafter emits a short "why this call" and a confidence; speculate only above a threshold | Calibration (ECE), precision/recall of speculation at each threshold, analysis of wrong guesses |

**Baselines.** No speculation. Heuristic "most likely next tool" table. Large prompted drafter (Speculative Actions
style). **Ablations:** no policy gate, no retrieval, untuned drafter, lossless vs lossy (results hidden vs shown).

**Data / environment (all public).**
- τ-bench and τ²-bench (Sierra Research, open source): airline, retail, telecom tasks with a simulated user, a
  database with ground-truth end state, and written domain policies. https://github.com/sierra-research/tau2-bench
- Trajectories for training the drafter: generate them by running an API model on the train split; optionally add
  public function-calling data (e.g. Salesforce xLAM / APIGen) for warm-up.
- Tool latency is near zero in the simulator, so inject realistic latency (e.g. 300 ms to 2 s per tool) and report
  time saved on the critical path, not raw wall-clock over an API.

**Cost trick.** In lossless mode the agent's behaviour doesn't change, so you record agent trajectories once and
score every drafter offline by replaying them. Only the lossy/anchoring experiment needs fresh live agent runs.

**Compute estimate (rough, check current prices).**
- Drafter QLoRA on a free Colab/Kaggle T4: ~1 to 3 GPU-hours per run, ~4 runs.
- Recording trajectories: a few hundred tasks with a small API model, roughly 20M to 40M tokens.
- Lossy/anchoring live runs: ~100 tasks × 3 configs × 2 trials ≈ 30M to 60M tokens.
- Total API roughly $30 to $80 with a small hosted model.

**Risks / fallback.** Hit@1 may be low (prior work sees 20% to 60%). Fallback: report tool-name-only speculation
plus argument repair, and the anchoring result stands on its own even if speed-ups are small.

## Comparison with the NDA pick
| | NDA review agent | Speculative tool calling |
|---|---|---|
| Novelty risk | Medium | High (very active area in 2026) |
| Ground truth | Exact (planted defects) | Exact (recorded next call, τ-bench end states) |
| Fit to all 5 capabilities | Natural | Tool/agentic/fine-tune natural, RAG/reasoning need care |
| Cost | Lowest | Low (offline replay) |
| "Cool factor" / systems flavour | Lower | Higher |
