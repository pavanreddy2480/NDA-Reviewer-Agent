# Option 4: "I couldn't find it" is not "it doesn't exist"
## Agents that can prove absence with retrieval and tools

Earlier options are still in docs/archive/ideas/01-nda-review-agent.md, docs/archive/ideas/02-speculative-tools.md and
docs/archive/ideas/03-tool-calling-rag.md.

---

## Objective (one paragraph)
Build an assistant that doesn't wrongly tell you "no, it isn't there" when you ask it to find something, and
show that it makes far fewer of those mistakes than today's search assistants. Today's assistants look at the top
few results and answer "no" with confidence when the item is just worded differently, on page 3, or in a folder
they didn't search. Our agent treats "no" as something it has to prove first: it searches by meaning, then by
exact keywords, filters and every page of results, and checks which places it couldn't search. Only then does it
answer "not found, here's what I checked" or "I can't be sure". **Success metric: the false-"no" rate**, measured
exactly by asking each question twice, once with the item present and once with it deleted, without raising the
false-"yes" rate.

---

## The everyday pain point
People constantly ask assistants questions whose honest answer is "no, there isn't one":
- "Did my landlord ever agree in writing to return the deposit?"
- "Have I already paid this invoice?" (if no, the agent pays it)
- "Is there already a GitHub issue for this bug?" (if no, the agent files a new one)
- "Did the professor post anything about the exam moving?"
- "Am I already subscribed to this service?"

RAG fails here in a specific way. Top-k retrieval always returns *something*, so the model either:
1. **False absence:** says "no" because the real item wasn't in the top-k, used different words ("Mr. Sharma"
   instead of "landlord"), sat in an unindexed folder, was cut off by a truncated or paginated tool result, or
   was filtered by permissions. This is the dangerous one: it leads to paying twice, filing duplicates, or
   telling a tenant they have no written proof when they do.
2. **False presence:** grabs a near miss ("landlord said he'd *think about* the deposit") and says "yes".

Today's agents report "no results" as if it proves non-existence. They don't distinguish wrong search scope, bad
query, stale index, truncated output and permission filtering from genuine absence.

## Is it already solved? (checked Oct 2026)
- **CROWN, "When Absence Is Evidence"** (Aug 2026, https://arxiv.org/abs/2608.04591): shows LLMs wrongly conclude
  "no" from partial evidence, and that rules, chain-of-thought and structured prompting only shift the errors
  around. But it studies **pure reasoning over context that is handed to the model**. It does not cover an
  agent that has to *go and establish* coverage with retrieval and tools. That is the open gap this project
  fills.
- AbstentionBench (https://arxiv.org/abs/2506.09038) and information-sufficiency work
  (https://arxiv.org/abs/2512.06476) cover "the question can't be answered", not "prove the thing isn't there".
- A 2026 practitioner write-up (https://tianpan.co/blog/2026/04/23/no-results-is-not-absence-agent-retrieval-negation)
  names the problem for agents and cites no benchmark or method for it.
- EnronQA (https://arxiv.org/abs/2505.00263) gives personal email RAG questions, but only positive ones.

I found no paper on agents that certify absence over a real corpus using tools. That was a careful search but
not exhaustive, so the team should still do its own related-work pass.

---

## Research question
Can a retrieval agent that treats "it doesn't exist" as a claim needing proof cut false-absence and
false-presence rates compared with standard agentic RAG, at a bounded extra cost? The agent searches in steps,
moving from semantic search to exhaustive tool checks, verifies its coverage, and either issues an **absence
certificate** or says what it couldn't check.

**Hypothesis:** standard RAG agents have a high false-absence rate that rises with aliasing, truncation and
scope gaps. The certificate agent lowers it substantially without raising false presence.

## The method: "absence certificate" agent
1. **Decompose the claim (reasoning).** "Landlord agreed to return deposit" becomes entities with aliases (name,
   company, email address), the time window, the communication channels, and what counts as "agreed".
2. **Semantic retrieval (RAG)** with query expansion over the aliases.
3. **Discriminate near misses (fine-tuned model).** A small LoRA-tuned verifier labels each candidate:
   true match, near miss or unrelated.
4. **Escalate to exhaustive tools (tool calling)** when nothing passes. These include keyword/regex search,
   metadata filters (sender, date range, folder), COUNT queries, and paginating to the end of a result instead
   of reading only page 1.
5. **Check coverage (tool calling + agentic).** Tools report which folders are indexed, when the index was last
   refreshed, whether results were truncated, and whether permission filters applied. The agent keeps a ledger
   of the scope it has covered.
6. **Decide (agentic).** It returns one of three outputs: "Found, with citation", "Not found, with a certificate
   listing the scope covered", or "Can't be sure, here's what I couldn't check". Only after a certificate may it
   take the follow-up action (pay the invoice, file the issue), and that action needs user confirmation.

## The five capabilities and how each is measured
| Capability | Why the problem needs it | Metric |
|---|---|---|
| RAG | Finding the item when it exists, under different wording | Recall@k on present cases; near-miss rate among retrieved items |
| Tool calling | Top-k can't prove absence; exhaustive and coverage tools can | Tool-call accuracy, argument validity (filters, dates), pagination completed, recovery after errors; **unsafe action rate** = acting on a false absence (duplicate payment or issue) |
| Reasoning | Turning a claim into a checkable scope (aliases, window, channels) | Scope-decomposition accuracy against gold aliases and windows; analysis of which step broke on each failure |
| Agentic | Planning a search budget, tracking covered scope, deciding when to stop or escalate to the user | False-absence and false-presence rates, calibration of "can't be sure", tool calls used per question |
| Fine-tuning | Cheap, accurate near-miss checker run on many candidates | Match vs near-miss F1 for a tuned 1.5B–3B model compared with a large prompted model |

## The evaluation design (the main novelty)
**Paired counterfactual deletion.** Every question exists twice: once over the full corpus (answer "yes, here")
and once with the target documents removed (true answer "no"). Same question, same corpus otherwise, so the
false-absence and false-presence rates are measured exactly.

**Stress factors you inject**, each a controlled condition:
- **Aliasing:** the item uses a different name or wording than the question.
- **Truncation and pagination:** the item is on page 3 of results, or past a tool's output limit.
- **Scope gaps:** the item is in a folder the index doesn't cover.
- **Stale index:** the item arrived after the last index refresh.
- **Permission filtering:** the item exists, but the tool hides it.
- **Near-miss distractors:** "said he'd think about it" vs "agreed".

## Data (all public)
- **Personal email (main domain):** the Enron email corpus (about 500k real emails) and EnronQA's
  question generation (https://arxiv.org/abs/2505.00263). Build about 300 question pairs on a few mailboxes.
- **Duplicate bug triage (second domain, for generalisation):** GitBugs (https://arxiv.org/abs/2504.09651,
  https://github.com/av9ash/gitbugs) has real bug reports with labelled duplicates across several projects. Ask
  "Is there already an issue for this?" with and without the original issue deleted. Here the unsafe action is
  filing a duplicate.
- **External check:** run your near-miss verifier on CROWN-Real to compare with the reasoning-only setting.

## Baselines and ablations
- **Baselines:** plain top-k RAG; a ReAct agent with the same tools but no certificate step (the "normal" agent);
  optionally a large model given the whole mailbox in its context window, as a reference point.
- **Ablations:** remove each of the following in turn: query expansion, exhaustive tools, coverage tools,
  the tuned verifier (swap in the prompted one), and the certificate requirement. Report results for each stress
  factor separately.

## Compute estimate (rough, check current prices)
- Embeddings and indexing: local, free.
- QLoRA near-miss verifier (Qwen2.5-1.5B or 3B) on a free Colab or Kaggle T4: about 2–3 GPU-hours per run, about
  3 runs. Training pairs can come from EnronQA and GitBugs duplicate/non-duplicate labels.
- Agent runs: about 600 items (300 pairs) plus 200 bug items, × 5 configs × about 10k tokens ≈ 40M tokens, roughly
  $20–50 with a small hosted model.
- LLM judge: only for deciding whether a found email really "agrees". Validate it against about 100 human labels,
  as the brief requires.

## Safety plan
- Use only public corpora (Enron, GitBugs). Use mock pay and file tools that never touch real systems.
- No real personal data. Enron is public, but it still has personal details, so report aggregate results only
  and quote nothing sensitive.

## Risks and fallback
- **Building question pairs takes effort.** Start with 3 question templates and 2 stress factors, then add more.
- **The certificate agent may be too slow or costly.** Report the cost against false-absence trade-off curve; that
  is itself a useful result.
- **If one domain is weak,** the paired-deletion benchmark is still a reusable contribution on its own.

## Why a TA should find it non-naive
- It targets a failure everyone has met but no one has a method or benchmark for in the agentic setting.
- The evaluation design (paired deletion plus injected stress factors) gives exact ground truth, not an LLM's
  opinion.
- RAG and tool calling are essential, not decoration: the research question is exactly when retrieval alone is
  insufficient and tools are needed to close the gap.
- It extends a very recent paper (CROWN, Aug 2026) in the direction its own setup leaves open.
