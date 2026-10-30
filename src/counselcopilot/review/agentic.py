"""Agentic evidence search: a second look at a rule the first search could not settle.

A clause that is not retrieved looks absent, so a miss in the fixed rule query becomes a false
omission (review problem 11). When a reverse check comes back unsettled, an agent searches the
NDA again with queries of its own: synonyms, legal phrasing, the opposite obligation.

The agent only finds segments, it never judges them. The same check primitive decides, on the
segments the fixed search found plus the agent's, so a difference from the `full` preset comes
from retrieval alone. Its tools are read-only and NDA text is data to it, so text planted in an
NDA can at worst change which segments the checker sees.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..data.draft import Draft
from ..llm import LLMClient, PendingBatch
from ..policy.schema import Rule
from ..retrieval.index import HybridIndex
from ..tools.agent import run_agent
from ..tools.registry import Tool, ToolRegistry

K_RESULTS = 5  # new segments per search
SEARCH_CHARS = 240  # per segment, so a whole search result survives the agent's 2000-character limit
MAX_READ = 4
READ_CHARS = 450

INSTRUCTIONS = """You help review a non-disclosure agreement (NDA). A first search found no clear evidence about one contract term. The NDA may still deal with it in other words, across several clauses, or somewhere unexpected.

Search for the segments that address the term. Try different wording each time: synonyms, legal phrasing, the opposite obligation, what the clause would be headed. Searches never return segments that were already checked, so a search that returns nothing relevant means you should change the words or stop.

You do not decide whether the NDA satisfies the term; someone else reads the segments you pick. Pick only segments that really deal with the term. If none do, finish with an empty list: that is a normal outcome.

Finish with args {"segments": [<segment numbers>]}."""


@dataclass
class EvidenceSearch:
    segments: list[int]  # new segments for the checker, none of them already shown
    queries: list[str] = field(default_factory=list)
    steps: int = 0
    stopped: str = "finish"  # finish | max_steps | bad_output | error


def _registry(draft: Draft, index: HybridIndex, shown: set[int], seen: dict[int, None]) -> ToolRegistry:
    reg = ToolRegistry()

    def search_nda(query: str) -> list[dict]:
        n = len(shown) + K_RESULTS  # asking for this many leaves K_RESULTS once `shown` is dropped
        ids = [int(h.passage.id) for h in index.search(query, k=n, candidates=n)]
        new = [i for i in ids if i not in shown][:K_RESULTS]
        seen.update(dict.fromkeys(new))
        return [{"segment": i, "text": draft.segments[i][:SEARCH_CHARS]} for i in new]

    def read_segments(segments: list) -> list[dict]:
        ids = [i for i in segments if type(i) is int and 0 <= i < len(draft.segments)][:MAX_READ]
        seen.update(dict.fromkeys(i for i in ids if i not in shown))
        return [{"segment": i, "text": draft.segments[i][:READ_CHARS]} for i in ids]

    s = lambda **p: {"type": "object", "properties": p, "required": list(p), "additionalProperties": False}
    reg.register(Tool("search_nda", "Keyword search over the NDA. Returns up to 5 segments not checked yet.",
                      s(query={"type": "string"}), search_nda))
    reg.register(Tool("read_segments", "Full text of up to 4 segments by number, e.g. the ones around a hit.",
                      s(segments={"type": "array", "items": {"type": "integer"}}), read_segments))
    return reg


def search_evidence(llm: LLMClient, rule: Rule, query: str, draft: Draft, index: HybridIndex, shown: list[int],
                    max_steps: int = 4, max_segments: int = 8, temperature: float = 0.0,
                    seed: int = 0) -> EvidenceSearch:
    """Find segments for `rule` beyond `shown`. Anything that goes wrong leaves no new segments."""
    seen: dict[int, None] = {}  # what the tools returned, in order; the agent can only pick from this
    reg = _registry(draft, index, set(shown), seen)
    task = (f"TERM: {rule.check_term}\nRULE: {rule.title}\nFIRST SEARCH: {query}\n"
            f"The NDA has {len(draft.segments)} segments; {len(shown)} were already checked.")
    try:
        res = run_agent(llm, reg, INSTRUCTIONS, task, max_steps=max_steps, tag="agentic_search",
                        temperature=temperature, seed=seed)
    except PendingBatch:
        raise
    except Exception:  # like a failed check: the first result stands, the review carries on
        return EvidenceSearch([], stopped="error")
    picked = res.final.get("segments") if res.stopped == "finish" else None
    # out of steps or no usable answer: what the searches turned up is still worth checking
    ids = [i for i in picked if type(i) is int and i in seen] if isinstance(picked, list) else list(seen)
    queries = [c.args["query"] for c in res.calls if c.name == "search_nda" and c.status == "ok"]
    return EvidenceSearch(ids[:max_segments], queries, res.steps, res.stopped)
