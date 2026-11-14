"""One NDA under several presets, side by side: which findings change and what the change costs.
A quick look for one document; scored comparisons across a split come from `cc rq1`, one run per
preset. Tokens include cached calls, so the preset that happens to run first gets no advantage."""

from __future__ import annotations

from ..data.draft import Draft
from ..llm import LLMClient
from ..policy.schema import DealContext, LawPack, PolicyPack
from ..review.policy_reviewer import PolicyReviewer, ReviewConfig


def _spent(llms: list[LLMClient]) -> tuple[int, int]:
    """(model calls, tokens) so far, cached ones included."""
    us = [llm.total_usage() for llm in llms]
    return (sum(u.calls for u in us),
            sum(u.input_tokens + u.output_tokens + u.cached_input_tokens + u.cached_output_tokens for u in us))


def compare_presets(llm: LLMClient, pack: PolicyPack, draft: Draft, deal: DealContext, presets: list[str],
                    law_pack: LawPack | None = None, checker_llm: LLMClient | None = None,
                    max_workers: int = 8) -> dict:
    llms = [llm, checker_llm] if checker_llm else [llm]
    summary, types = {}, {}
    for name in presets:
        cfg = ReviewConfig.preset(name)
        cfg.max_workers = max_workers
        calls, tokens = _spent(llms)
        res = PolicyReviewer(llm, pack, cfg, law_pack=law_pack, checker_llm=checker_llm).review(draft, deal)
        calls_now, tokens_now = _spent(llms)
        summary[name] = {"findings": len(res.findings), "checks": res.n_checks, "agent_searches": res.n_agent_searches,
                         "check_errors": res.n_errors, "model_calls": calls_now - calls, "tokens": tokens_now - tokens}
        types[name] = {}
        for f in res.findings:  # one rule can have two finding types; show both
            types[name].setdefault(f.rule_id, []).append(f.type.value)
    rules = {rule: {name: "+".join(types[name].get(rule, [])) or "-" for name in presets}
             for rule in sorted({r for t in types.values() for r in t})}
    return {"presets": summary, "rules": rules,
            "differs": [rule for rule, row in rules.items() if len(set(row.values())) > 1]}


def format_comparison(cmp: dict) -> str:
    presets = list(cmp["presets"])
    width = max(18, *(len(p) + 2 for p in presets))
    first = max(20, *(len(r) + 4 for r in cmp["rules"]), 16)

    def line(label: str, cells: list) -> str:
        return f"{label:<{first}}" + "".join(f"{c!s:<{width}}" for c in cells).rstrip()

    out = [line("rule", presets)]
    out += [line(f"{rule}{' *' if rule in cmp['differs'] else ''}", list(row.values()))
            for rule, row in cmp["rules"].items()]
    if not cmp["rules"]:
        out.append("no findings under any preset")
    out.append("")
    for key in ("findings", "checks", "agent_searches", "check_errors", "model_calls", "tokens"):
        out.append(line(key, [cmp["presets"][p][key] for p in presets]))
    out.append(f"\n{len(cmp['differs'])} rule(s) differ (marked *)")
    return "\n".join(out)
