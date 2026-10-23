# NOMOS vs CounselCopilot: is there an overlap?

> **Historical document.** Kept as a record of its date. The current design is `newdesign.md` (v6; §19 lists the 22 Oct 2026 audit fixes), and the current proposal is `proposal/proposal.tex`.

Checked on 9 Oct 2026 against the full text of `NOMOS.pdf` (arXiv 2610.11030, "Compiling Written Policies into
Statically Verified Tool-Call Gates for LLM Agents", 28 pages).

## Verdict

**No overlap with our red-team and repair loop, and no overlap with RQ1.** NOMOS is not about contracts, drafting or
redlines at all. Our earlier note called it "a result about agentic redlining"; that was wrong. Nothing in the
proposal needs to change. At most it is one related-work citation.

## What NOMOS does, in plain words

- **Setting:** an AI agent that calls tools (book a flight, refund an order, send money) must obey a written policy,
  e.g. an airline's rules.
- **Method:** an LLM reads the policy once and extracts candidate rules. A compiler then checks those rules against
  the tool schemas, with no LLM, solver or prover:
  - Does a rule block itself (deadlock)?
  - Does it name arguments the tool doesn't have?
  - Can it ever be satisfied?
  - Do two rules contradict each other?
  - Does it guard the wrong tools?
  Defective rules are repaired or rejected. Surviving rules become a fixed gate that allows or refuses each tool call
  at runtime.
- **Evaluation:** τ²-bench (airline, retail) and AgentDojo (prompt-injection attacks). Policy violations drop from
  66.3% to 2.6% on airline, and banking injection attacks drop to 0%.

## Side by side

| Question | NOMOS | CounselCopilot |
|---|---|---|
| What is checked? | An agent's **tool calls** at runtime | A **contract draft** (NDA) |
| What is "repaired"? | **The compiled rules**, when they are malformed | **The document**: clause-level redlines |
| Who is the attacker? | Prompt injection from AgentDojo, an external threat to block | Our own **opposing-counsel agent**, used as a tool to find loopholes in the draft |
| Is there a loop? | No: compile once, enforce deterministically | Yes: attack → repair → regression check, up to 3 rounds |
| Cross-rule checking? | Yes, but only to find contradictory *rules* at compile time | Yes: re-run *all* rules on the *repaired draft* to catch new violations |
| Deal applicability (RQ1)? | No | Yes |
| Legal domain, India, NDAs? | No | Yes |

## Two useful things it gives us

1. **A name collision to avoid.** NOMOS cites a *different* paper also called PolicyGuard: Kang, Yu and Hwang,
   "PolicyGuard: A dialogue-grounded…", which guards agent tool calls. Ours is Malik, Singh and Azad, arXiv 2606.32004,
   on NDAs. In the proposal, always cite ours with its arXiv number so the TA doesn't confuse the two.
2. **It supports a design choice.** NOMOS shows that LLM-extracted rules are often defective: 37% of raw candidates on
   airline and 13% on retail. That is extra support for our policy compiler validating every rule before use. It also
   supports scoring with an **independent checker**, not the system's own rules, which is what we already do for RQ2.

## What to change

- **Optional:** add one line to related work: "Policy compilation for agents (NOMOS, VeriGuard, ToolGuard) turns
  written policies into tool-call gates. We apply policies to *documents* and repair the document, not the rules."
- Nothing else. The novelty argument against the TA's comment stands as written in `novelty_check_vs_prop.md`.
