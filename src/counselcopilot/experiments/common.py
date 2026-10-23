from __future__ import annotations

import json
import time
from pathlib import Path

from ..llm import LLMClient


def run_dir(name: str, root: str | Path = "runs") -> Path:
    d = Path(root) / f"{time.strftime('%Y%m%d-%H%M%S')}-{name}"
    d.mkdir(parents=True, exist_ok=True)
    return d


def write_jsonl(path: Path, rows: list[dict]) -> None:
    with path.open("w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")


def usage_report(llm: LLMClient) -> dict:
    t = llm.total_usage()
    return {
        "backend": llm.name,
        "model": llm.model,
        "calls": t.calls,
        "cached_calls": t.cached_calls,
        "input_tokens_uncached": t.input_tokens,
        "output_tokens_uncached": t.output_tokens,
        "cost_usd_uncached": round(llm.cost(), 4),
        "cached_input_tokens": t.cached_input_tokens,
        "cached_output_tokens": t.cached_output_tokens,
        # list price with an empty cache: compare presets on this, not on the uncached cost
        "cost_usd_full": round(t.full_cost(llm.price_in, llm.price_out), 4),
        "by_agent": {k: vars(v) for k, v in llm.usage().items()},
    }
