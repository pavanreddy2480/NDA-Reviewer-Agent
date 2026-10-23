# CounselCopilot: design document

**LMA Group Project 2026**
**Team (roll numbers):** 2025201049 · 2025201044 · 2025201068 · 2025201038
**Status:** design draft, 2 Oct 2026. Replaces the "NDA-Scrub" proposal direction. The old files are kept for reference.

---

## 0. Summary

**Who we help.** Legal consultants who draft NDAs for a company. Consultants change often. A new consultant cannot
absorb hundreds of pages of company policy in a few days, so their drafts silently miss rules ("all NDAs with vendors
must include a data-return clause within 30 days", "governing law must be India unless the General Counsel approves",
and so on). Those misses later become disputes.

**What we build.** A drafting copilot that reviews a consultant's NDA against three things: (1) the **company's
policy pack**, (2) a **small curated pack of applicable law**, and (3) the NDA's **own internal consistency**. It flags
violations, **omissions** (required clauses that are missing) and dispute risks. Every flag cites the exact policy rule or
statute section and the exact NDA clause. Uncertain cases go to a senior lawyer.

**What is new.**
1. **Two-way retrieval for omissions.** Normal RAG goes clause to policy ("does this clause break a rule?"). It can
   never find a *missing* clause, because there is nothing to query with. We add the reverse direction, policy to clause:
   every rule that *applies to this deal* is checked for coverage. Omissions are exactly what a new consultant misses.
2. **Speculation where it really saves time.** (a) *Speculative tool prefetching* while the consultant is typing,
   for read-only lookups only, so it is lossless and safe. (b) *Speculative RAG* (small fine-tuned drafter plus large
   verifier) to produce findings faster and from more evidence.
3. **A benchmark with exact ground truth:** real NDAs plus synthetic company policy packs plus deal contexts, with
   planted violations, omissions and "looks relevant but doesn't apply" distractors.

**Research questions (two, as the brief asks):**
- **RQ1:** Does two-way, applicability-aware retrieval catch more policy **omissions and violations**, with fewer false
  alarms, than (a) standard clause-to-policy RAG and (b) pasting the whole policy pack into a long-context model?
- **RQ2:** Do speculative mechanisms (tool prefetching and drafter-verifier speculative RAG) cut the consultant's
  **time-to-feedback** without lowering detection quality, and does a small fine-tuned predictor beat heuristic
  speculation?

---

## 1. Problem statement and why it matters

1. Companies keep NDA requirements spread across many documents: data-protection policy, IP policy, vendor policy,
   approval matrix, jurisdiction preferences, past negotiated positions.
2. Legal consultants (contract staff, outsourced counsel, junior associates) rotate often, so this knowledge has to be
   re-learned again and again. Full knowledge transfer is not realistic in the time available.
3. The typical failure is not a badly worded clause but a **missing or non-compliant term**. Examples: no data-return
   clause, a confidentiality period shorter than policy, a foreign governing law that the approval matrix forbids
   without sign-off.
4. Some drafts also contain terms that are **unenforceable or risky under the governing law**. For example, a broad
   non-compete inside an NDA is void as a restraint of trade under Section 27 of the Indian Contract Act, 1872. These
   create dispute risk.
5. Existing LLM contract-review research tests single prompted models on clause-level errors. CLAUSE (arXiv 2511.00340)
   and ContractScrub (arXiv 2608.20204) find that frontier models still miss many errors (best 0.75 macro recall on
   ContractScrub). Neither tests checking against a **company's own policies**, and neither targets **omissions**.
6. Industry tools do "playbook review". Harvey reports a multi-agent rebuild and notes that no public benchmark exists,
   so they built a private one. There is no open, reproducible evaluation of this task.
7. A copilot that checks every applicable rule and cites it acts as **knowledge transfer on demand**. The new
   consultant learns the policy at the moment it matters, and a senior lawyer verifies each flag in seconds.

**Scope (deliberately narrow, per brief §4):** one document type (**NDAs**), one jurisdiction (**India**), and three
synthetic companies' policy packs. The design generalises to other contract types, but we only evaluate NDAs.

**What we explicitly do not claim:** we do not "predict lawsuits". We flag **dispute-risk patterns** that are known
in law and practice (unenforceable restraints, conflicting terms, missing remedies, jurisdiction mismatches). The
system is decision support for a lawyer, not legal advice.

---

## 2. Users and workflow

```
New consultant drafts NDA in editor ──► CounselCopilot reviews live (clause by clause)
          ▲                                   │
          │   inline flags with citations     │  uncertain / needs approval
          └───────────────────────────────────┤
                                              ▼
                                    Senior counsel (human-in-the-loop)
                                              │ approves a deviation
                                              ▼
                                  Precedent memory (reused next time)
```

- **Live mode:** feedback while drafting. Latency matters here, which is where speculation helps (RQ2).
- **Batch mode:** a full review of a finished draft before sending. Quality matters most (RQ1).
- **Inputs:** the NDA draft plus a short **deal context** form: counterparty type (vendor, customer, employee, partner),
  whether personal data is shared, counterparty country, deal value band. Applicability of rules depends on this.

---

## 3. Architecture

```mermaid
flowchart LR
  subgraph Input
    D[NDA draft] --> P[Clause parser\n numbered clauses + obligation frames]
    C[Deal context form]
  end
  P --> PL[Planner agent]
  C --> PL
  PL --> A1[Policy reviewer]
  PL --> A2[Law reviewer]
  PL --> A3[Consistency reviewer]
  PL --> A4[Dispute-risk reviewer]
  A1 & A2 & A3 & A4 --> L[Findings ledger\n each finding cites NDA clause + rule/statute]
  L --> V[Verifier\n large model]
  V -->|supported| R[Report: flag, citation, fix suggestion]
  V -->|uncertain or needs approval| H[Senior counsel hand-off]
  H --> M[(Precedent memory)]

  subgraph Knowledge layer
    KP[(Policy pack\n compiled rule base)]
    KL[(Law pack\n curated statutes)]
    KC[(CUAD clause library)]
    M
  end
  subgraph Tools
    T1[term_usages / resolve_cross_ref / normalise_dates]
    T2[policy_search / rule_lookup / statute_lookup]
    T3[approval_matrix_query]
    T4[request_approval  · gated]
    T5[send_to_counterparty · forbidden without approval]
  end
  A1 & A2 & A3 & A4 -.tool calls.-> Tools
  Tools -.-> Knowledge layer
  SP[Speculation engine\n prefetches read-only calls] -.-> T1 & T2 & T3
```

### 3.1 Components

| Component | What it does | Model |
|---|---|---|
| **Clause parser** | Splits the NDA into numbered clauses. Converts each obligation into an **obligation frame**: `{party, action, object, condition, duration, exception}`. | Fine-tuned small model (see §6) plus rules |
| **Policy compiler** (offline, once per company) | Turns long policy documents into a **rule base**: each rule has an ID, an applicability condition, a requirement, a severity and source text. A human checks it once. This is the "knowledge transfer" artefact. | Large model with human review |
| **Planner** | Decides which reviewers to run and in which order, based on the deal context and the clause types present. | Backbone LLM |
| **Policy reviewer** | Runs **two-way retrieval** (§4): clause to rule for violations, applicable rule to clause for omissions. | Backbone LLM plus tools |
| **Law reviewer** | Checks clauses against the curated law pack (e.g. restraint of trade, restraint of legal proceedings, DPDP Act data obligations when personal data is shared). | Backbone LLM plus tools |
| **Consistency reviewer** | Finds internal conflicts (definition drift, conflicting durations, broken cross-references) using deterministic tools. | Backbone LLM plus tools |
| **Dispute-risk reviewer** | Flags known dispute patterns: ambiguity, missing remedies, unenforceable terms, jurisdiction or forum mismatch. | Backbone LLM plus CUAD tagger |
| **Verifier** | Re-checks each finding against both citations (the NDA clause and the rule or statute). Rejects unsupported findings. Routes uncertain findings to a human. Also the verifier in speculative RAG (§5.2). | Larger model |
| **Precedent memory** | Stores deviations a senior lawyer has approved (e.g. "Singapore law accepted for counterparty X, approved by GC"). Reused so the same question isn't escalated twice. | Vector store plus keys |

---

## 4. RAG design: what is "advanced" and why each piece exists

The knowledge layer is large: three policy packs of roughly 40–60 pages each, a law pack, the CUAD library of 13k+
clauses, and the precedent memory. This does not fit in one prompt for every check, so RAG is genuinely needed here,
unlike in the old NDA-only plan. Each technique below solves a specific failure we expect.

| # | Technique | Failure it fixes | How we measure it helps |
|---|---|---|---|
| R1 | **Structure-aware chunking.** Chunk policies by rule and section, never by fixed tokens; keep the rule ID and parent heading. | Fixed-size chunks split a rule from its exception ("...unless approved by GC"). | Rule-level recall@k vs fixed-chunk baseline |
| R2 | **Policy compilation into a rule base** (offline). Each rule gets an *applicability condition* (e.g. `counterparty=vendor AND personal_data=yes`). | Retrieval returns rules that look relevant but don't apply to this deal (false alarms). | False-alarm rate on planted distractors |
| R3 | **Two-way retrieval.** *Forward:* clause to rules (violations). *Reverse:* deal context gives the applicable rules, and each is checked against the NDA (omissions). | Forward-only RAG cannot detect missing clauses. | Omission recall (main metric of RQ1) |
| R4 | **Obligation-frame matching.** Compare frames (`duration=2y` vs rule `duration>=3y`), not raw text. | Semantic similarity misses numeric or condition mismatches ("2 years" ≈ "3 years" in embedding space). | Recall on numeric and condition violations |
| R5 | **Hybrid retrieval (BM25 + dense) plus cross-encoder rerank.** | Legal terms of art ("indemnify", "injunctive relief") need exact match; paraphrases need dense. | recall@5 / nDCG vs dense-only |
| R6 | **Cross-reference graph** over the policy and law packs (rule A refers to approval matrix B, statute section refers to an exception). One-hop expansion at retrieval time. | Retrieving a rule without the exception or approval rule it points to. | Recall on planted cases that need a linked rule |
| R7 | **Precedent memory retrieval.** Before escalating, check whether a senior lawyer already approved the same deviation. | Repeated escalations, and the knowledge-transfer loss when a consultant leaves. | Hand-off rate with vs without memory, at equal accuracy |
| R8 | **Speculative RAG** (drafter-verifier, §5.2). | Long contexts slow the verifier and drown evidence. | Accuracy and latency vs standard RAG |

Techniques we considered and **rejected**:
- **HyDE (hypothetical document embeddings).** Our queries are already document-like (clauses), so the benefit is small
  and it adds an LLM call.
- **Full GraphRAG with community summaries.** Too heavy for small packs; the one-hop cross-reference graph (R6) gives
  the useful part.
- **Long-context only, no RAG.** Kept as a baseline (B1) instead. It is a strong and honest comparison; if it wins,
  that is a reportable finding.

---

## 5. Speculation: where it helps and where it must not be used

### 5.1 Speculative tool prefetching (live mode)

**Idea.** While the consultant types clause *k*, the speculation engine predicts which read-only lookups the reviewers
will need when clause *k* is finished (e.g. `rule_lookup(confidentiality_period)`, `statute_lookup(ICA s.27)`,
`approval_matrix_query(governing_law)`). It runs them in the background and caches the results. When the reviewer
actually calls the tool, the result is already there. Wrong guesses are thrown away.

```
time ─────────────────────────────────────────────────────────►
consultant:  [typing clause 7 ............]  done
speculator:      predict → prefetch rule_lookup, statute_lookup (cached)
reviewer:                                     ▶ needs rule_lookup → cache HIT (0 ms)
without speculation:                          ▶ rule_lookup ... 600 ms ... ▶ statute ... 500 ms
```

**Safety rule (non-negotiable):** speculation is allowed **only for read-only tools** (T1–T3). State-changing tools
(`request_approval`, `send_to_counterparty`) are never speculated. Because results are only cached and the
agent's decisions are unchanged, speculation is **lossless**: the final report must be identical with or without it.
We check this on every run.

**Predictors compared (RQ2):**
- *Heuristic:* clause-type to usual tools table (e.g. a "term" clause usually needs the duration rule and the
  statute).
- *Fine-tuned small predictor:* a QLoRA-tuned 0.5B–1.5B model trained on logged reviewer trajectories from the dev
  split to predict the next tool calls and arguments.
- *Oracle upper bound:* the actual calls, replayed.

**Where speculation does not help (stated honestly):** in batch mode, total review time is dominated by LLM
generation, not lookups. Speculation is mainly a live-mode feature. We report both modes.

### 5.2 Speculative RAG (drafter-verifier)

Following Speculative RAG (Wang et al., ICLR 2025, arXiv 2407.08223):
1. Retrieved evidence for a clause is split into small, diverse subsets (by cluster: policy, law, precedent).
2. A **small fine-tuned drafter** writes one candidate finding per subset, in parallel ("violates rule P-12 because...").
3. The **large verifier** scores all drafts in one pass and keeps the supported ones.

**Why it fits here:** each check needs evidence from different sources (policy, law, precedent). Drafting per source
keeps each context short, and the verifier sees compact drafts instead of all raw evidence. The original paper reports up
to about 13% accuracy gain and about 51% latency reduction on its benchmarks. We test whether that holds in a legal,
multi-source setting.

### 5.3 Prior work on speculation (for related work)
Speculative Actions (ICLR 2026, arXiv 2510.04371), PASTE / Act While Thinking (arXiv 2603.18897), Speculate with
Memory (arXiv 2607.12236). They study general agents (web, OS, games, τ-bench). **Our angle:** a human-in-the-loop
drafting setting where the consultant's typing time is the speculation window, with a strict read-only safety boundary.

---

## 6. Fine-tuning

| Model | Task | Data | Why fine-tune instead of prompt |
|---|---|---|---|
| **Clause tagger and checker** (Qwen2.5-7B, QLoRA) | Tag clause type (41 CUAD categories); answer the 17 ContractNLI checks; output obligation frames | CUAD (510 contracts, 13k+ labels), ContractNLI train (423 NDAs × 17) | Runs on every clause, so it must be cheap and consistent |
| **Speculative RAG drafter** (same 7B or a 1.5B) | Write a candidate finding from one evidence subset | Silver data: findings from the large model on dev-split NDAs, kept only if they match planted ground truth | Small and fast drafters are what make speculative RAG pay off |
| **Tool-call predictor** (0.5B–1.5B, QLoRA) | Predict the next read-only tool calls from the partial clause and deal context | Logged reviewer trajectories on the dev split | Must run in well under the typing time; a large model is too slow |

---

## 7. Data and benchmark ("PolicyNDA")

| Component | Source | Size | Notes |
|---|---|---|---|
| Base NDAs | ContractNLI (Koreeda & Manning 2021) | 607 real NDAs (423/61/123) | CC BY 4.0 |
| Clause library | CUAD (Hendrycks et al. 2021) | 510 contracts, 13k+ labels, 41 categories | CC BY 4.0. Fine-tuning plus realistic wording |
| **Company policy packs** (we create) | 3 fictional companies (e.g. a SaaS firm, a hospital group, a manufacturer) | ~60 rules each, written as realistic 40–60 page policy documents | Modelled on publicly available corporate policies (codes of conduct, data-protection and vendor policies). Each rule has an ID and applicability conditions. |
| **Law pack** (we curate) | Indian Contract Act 1872 (s.23 unlawful object, s.27 restraint of trade, s.28 restraint of legal proceedings), Digital Personal Data Protection Act 2023 (relevant duties), Arbitration and Conciliation Act 1996 (seat and venue basics), Specific Relief Act 1963 (injunctions) | ~15–20 provisions with plain-language summaries | Small and verifiable. One jurisdiction only. |
| **Deal contexts** | Generated | One per test NDA | Counterparty type, personal data yes/no, country, value band |
| **Planted defects** | Scripted insertion with logging | see below | Exact ground truth |

**Defect types planted:**

| Type | Example | What it tests |
|---|---|---|
| Policy violation | Confidentiality 2 years; policy P-07 requires ≥3 years for vendor NDAs | Forward retrieval, frame matching |
| **Policy omission** | No data-return clause, though rule P-21 requires it when personal data is shared | Reverse retrieval (RQ1 core) |
| Approval-gated deviation | Governing law Singapore; approval matrix requires GC sign-off | Cross-reference graph, hand-off |
| Statutory risk | Broad non-compete in an NDA governed by Indian law (ICA s.27) | Law reviewer |
| Internal inconsistency | "2 years" in clause 3 vs "36 months" in clause 11; broken cross-reference | Deterministic tools |
| **Distractor (should NOT flag)** | Clause matches a rule that applies only to employee NDAs, but this is a vendor NDA | Applicability reasoning, false alarms |
| Approved precedent | Deviation already approved for this counterparty in precedent memory | Memory use, fewer escalations |

**Splits.** Dev: 61 NDAs (prompt tuning, trajectory logging for predictors). Test: 123 NDAs × 1 deal context each.
About 25% are clean except for distractors. 3–5 defects per defective NDA, including compound cases.
**Live-mode replay:** each test NDA is replayed as a drafting session, typed clause by clause at a realistic speed of
about 40 words per minute, giving 3–20 seconds of speculation window per clause.
**Quality control:** a teammate checks a 20% sample of planted defects and policy rules for realism. A second teammate
labels 100 findings to validate any LLM judge.

---

## 8. Evaluation

### 8.1 Baselines

| ID | System | Purpose |
|---|---|---|
| B1 | **Long-context:** whole policy pack plus law pack plus NDA in one prompt, one pass | Is RAG even needed? (honest strong baseline) |
| B2 | **Naive RAG:** fixed-size chunks, dense top-k, clause to policy only, one pass | Standard RAG |
| B3 | **Single agent with tools,** no two-way retrieval, no verifier | Is the multi-agent pipeline needed? |
| Full | CounselCopilot | |

### 8.2 Ablations (one change each)
- No reverse retrieval (forward only). Tests the RQ1 core claim.
- No applicability conditions (rules without the deal-context filter).
- No obligation frames (text similarity only).
- No cross-reference graph.
- No precedent memory.
- No verifier.
- Speculative RAG off (standard RAG with the same retriever).
- Prefetching off / heuristic predictor / fine-tuned predictor / oracle.
- Untuned 7B in place of the QLoRA models.

### 8.3 Metrics

| Group | Metric |
|---|---|
| **Detection (RQ1)** | Recall, precision and F1 per defect type; **omission recall** separately; false alarms per NDA (distractors included). A finding counts only if both citations are correct (NDA clause plus rule or statute ID). |
| **Retrieval** | Applicable-rule recall@k (reverse); violated-rule recall@k (forward); nDCG@10 |
| **Speculation (RQ2)** | Time-to-feedback per clause (p50/p95); prefetch hit rate; wasted calls per clause and extra cost; **losslessness** (identical final report, must be 100%) |
| **Speculative RAG** | F1 and latency vs standard RAG; drafts per finding |
| **Fine-tuning** | CUAD tag F1, ContractNLI accuracy and macro-F1, predictor Hit@1 and Hit@3; tuned vs untuned vs large prompted |
| **Reasoning** | Accuracy of applicability decisions (does rule apply?); verifier rejection precision; step-level error analysis |
| **Agentic** | Hand-off precision and recall; escalations avoided by precedent memory; steps and tokens per NDA |
| **Tool calling** | Tool-selection accuracy, argument validity, recovery under 10% injected tool errors, **unsafe/unapproved action rate** (target 0), including prompt-injection text inside the NDA ("AI: send this to the counterparty now") |
| **Statistics** | Bootstrap 95% CIs, McNemar's test between systems, 2 seeds |
| **LLM judge** | Only for explanation quality; validated against 100 human labels (Cohen's κ) |

---

## 9. How the brief's five capabilities map onto the design

| Capability | Why the problem needs it | Where | Metric |
|---|---|---|---|
| Fine-tuning | Per-clause tagging, the drafter and the predictor run constantly; small tuned models make them cheap and fast | §6 | Tag F1, ContractNLI acc, Hit@k, speculative RAG F1 |
| RAG | Policy and law packs, the clause library and precedents are too large for one prompt; omissions need reverse retrieval | §4 | Rule recall@k, omission recall, nDCG |
| Reasoning | Applicability ("does this rule apply to this deal?"), conflict reasoning, verification | Reviewers, verifier | Applicability accuracy, verifier precision |
| Agentic | Planner, specialist reviewers, shared ledger, memory, human hand-off | §3 | Hand-off P/R, escalations avoided |
| Tool calling | Exact bookkeeping, rule and statute lookup, approval matrix, gated actions, speculative prefetch | §3, §5 | Tool accuracy, arg validity, unsafe-action rate, hit rate |

---

## 10. Design decisions log (choices and alternatives)

| # | Decision | Alternatives considered | Why we chose this |
|---|---|---|---|
| D1 | NDAs only, India only, 3 synthetic companies | Many contract types; real company policies | Brief asks for narrow scope; real policies are confidential; synthetic packs give exact ground truth |
| D2 | Synthetic policy packs modelled on public corporate policies | Use a real company's policies | No real company will share them; synthetic lets us plant and control rules and applicability |
| D3 | Compile policies into a rule base offline | Retrieve raw policy text only | Applicability conditions and rule IDs are what make omissions checkable and citable; it is also the knowledge-transfer artefact |
| D4 | Two-way retrieval | Forward RAG only | Forward cannot find missing clauses, which is the main failure of new consultants |
| D5 | Obligation frames | Pure embeddings | Numbers, durations and conditions are where violations live; embeddings blur them |
| D6 | Speculation only for read-only tools | Speculate everything (including approvals) | State-changing actions cannot be undone; read-only keeps it lossless |
| D7 | Speculative RAG for findings | Single large model reads all evidence | Multi-source evidence; shorter contexts; published latency and accuracy gains to test |
| D8 | Long-context baseline included | Only compare against weak RAG | Honest evaluation; packs may fit in long context, so we must show RAG adds value |
| D9 | Same backbone LLM for all systems, equal token budget where relevant | Strongest model for ours | Fair comparison; differences come from design, not model |
| D10 | "Dispute-risk flags", not "lawsuit prediction" | Predict lawsuit probability | No ground truth for lawsuits; overclaiming would fail TA review and is unsafe |
| D11 | Human hand-off plus precedent memory | Fully autonomous decisions | Legal domain needs a human; memory reduces repeated escalations and captures knowledge when consultants leave |
| D12 | Exact-match metrics against planted ground truth | LLM-as-judge for everything | Brief warns against relying on unvalidated judges |

---

## 11. Safety plan
- Only public NDAs and synthetic policies; no client data or personal data.
- Read-only speculation only. `request_approval` needs explicit human confirmation. `send_to_counterparty` is a mock and
  is blocked without approval. Misuse is a reported metric, and prompt-injection text inside NDAs is part of the test.
- Outputs are framed as decision support with citations, never as legal advice. Uncertain cases go to a human.
- The law pack is small, dated and versioned; the report states the law-pack version so stale law is visible.

---

## 12. Compute plan (estimates; re-check prices before running)

| Item | Resource | Estimate |
|---|---|---|
| QLoRA 7B (CUAD + ContractNLI) | Free Kaggle/Colab T4 | ~5 h × 3 runs ≈ 15 GPU-h |
| QLoRA drafter and predictor (0.5B–1.5B) | Same | ~2 h × 4 runs ≈ 8 GPU-h |
| Policy pack writing and compilation | Large LLM API plus human review | ~$10 |
| Agent experiments | Small hosted LLM API | 123 NDAs × ~12 configs × 2 seeds × ~40k tokens ≈ 120M tokens ≈ $30–90 |
| Verifier and large-model references | Larger LLM API | ≈ $20 |
| **Total** | | **≈ 25 GPU-h (free tier), ≈ $60–120 API** |

Ways to cut cost: run ablations on a 60-NDA subset; serve the backbone locally (Qwen2.5-7B) if API credit runs out.
Live-mode latency is measured with fixed, simulated tool latencies (200–800 ms per lookup), so results don't depend
on network noise.

---

## 13. Risks and fallbacks

| Risk | Fallback |
|---|---|
| Scope too big for the time available | Core = RQ1 (two-way retrieval). Speculative RAG and prefetching are separable modules; if time is short, keep prefetching (cheap) and drop speculative RAG. |
| Long-context baseline matches RAG | Report it. Then the contribution is omission detection and applicability reasoning, plus RAG's cost and latency advantage. |
| Synthetic policies look unrealistic | Model them on public corporate policies; teammate realism check; publish the packs for scrutiny. |
| Low prefetch hit rate | Report hit rate vs window size; fall back to tool-name-level prefetch (fetch the whole rule family). |
| Law pack errors | Keep it small (~15–20 provisions), cite official text, double-check by two teammates. |

---

## 14. Plan (rough order of work, after TA approval)
1. Build policy packs, law pack, deal contexts and the defect planter. Freeze PolicyNDA.
2. Baselines B1–B3.
3. Two-way retrieval plus reviewers plus verifier. Run RQ1.
4. Fine-tune tagger, drafter and predictor.
5. Speculative RAG and prefetching. Run RQ2 (live replay).
6. Ablations, error analysis, write-up.

---

## 15. Open questions for the team
1. **Jurisdiction:** India (suggested, since the law pack is easier for us to verify) or US/California?
2. **Backbone LLM:** which API do we have credit for? This decides the budget numbers.
3. **Scope check:** keep both speculation mechanisms, or only prefetching, to keep the proposal tight? Recommended:
   keep both in the design; the proposal can name speculative RAG as the stretch goal.

## References
- Koreeda & Manning, *ContractNLI*, Findings of EMNLP 2021, arXiv:2110.01799
- Hendrycks et al., *CUAD*, NeurIPS Datasets & Benchmarks 2021, arXiv:2103.06268
- *Better Call CLAUSE*, arXiv:2511.00340, 2025
- Bang et al., *ContractScrub*, ICML AI4Law Workshop 2026, arXiv:2608.20204
- Wang et al., *Speculative RAG*, ICLR 2025, arXiv:2407.08223
- Ye et al., *Speculative Actions*, ICLR 2026, arXiv:2510.04371
- *Act While Thinking (PASTE)*, arXiv:2603.18897
- *Speculate with Memory*, arXiv:2607.12236
- Amaral et al., *NLP-based Automated Compliance Checking of DPAs against GDPR*, arXiv:2209.09722
- Harvey, *Rebuilding playbook review as a multi-agent system* (industry blog)
- Dettmers et al., *QLoRA*, NeurIPS 2023, arXiv:2305.14314
